from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from products.models import Product
from suppliers.models import Supplier
from supplies.models import Supply, SupplyProduct


class SupplyItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class SupplyProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='product_id', read_only=True)
    title = serializers.CharField(source='product.title', read_only=True)

    class Meta:
        model = SupplyProduct
        fields = ('id', 'title', 'quantity')


class SupplySerializer(serializers.ModelSerializer):
    products = SupplyProductSerializer(source='items', many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    supplier_inn = serializers.CharField(source='supplier.inn', read_only=True)

    class Meta:
        model = Supply
        fields = (
            'id',
            'supplier',
            'supplier_name',
            'supplier_inn',
            'delivery_date',
            'created_by',
            'products',
            'created_at',
        )
        read_only_fields = fields


class SupplyCreateSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField()
    delivery_date = serializers.DateField(required=False, allow_null=True)
    products = SupplyItemSerializer(many=True)

    def validate_products(self, value):
        if not value:
            raise serializers.ValidationError('Укажите хотя бы один товар.')
        ids = [item['id'] for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError('Один и тот же товар указан в поставке дважды.')
        return value

    def create(self, validated_data):
        company_id = self.context['request'].user.company_id
        items = validated_data['products']
        product_ids = [item['id'] for item in items]
        delivery_date = validated_data.get('delivery_date') or timezone.localdate()

        with transaction.atomic():
            try:
                supplier = Supplier.objects.get(
                    pk=validated_data['supplier_id'],
                    company_id=company_id,
                )
            except Supplier.DoesNotExist:
                raise serializers.ValidationError(
                    {'supplier_id': 'Поставщик не найден в вашей компании.'}
                )

            locked = {
                product.id: product
                for product in Product.objects.select_for_update().filter(
                    id__in=product_ids,
                    storage__company_id=company_id,
                )
            }
            missing = [product_id for product_id in product_ids if product_id not in locked]
            if missing:
                raise serializers.ValidationError(
                    {'products': f'На складе клмпании нет товаров с id: {missing}.'}
                )
            supply = Supply.objects.create(
                supplier=supplier,
                delivery_date=delivery_date,
                created_by=validated_data['created_by'],
            )
            for item in items:
                product = locked[item['id']]
                SupplyProduct.objects.create(
                    supply=supply,
                    product=product,
                    quantity=item['quantity'],
                )
                product.quantity += item['quantity']
                product.save(update_fields=['quantity'])
        return supply