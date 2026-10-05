from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from products.models import Product
from sales.models import Sale, ProductSale


class ProductSaleItemSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class ProductSaleSerializer(serializers.ModelSerializer):
    product = serializers.IntegerField(source='product_id', read_only=True)
    title = serializers.CharField(source='product.title', read_only=True)

    class Meta:
        model = ProductSale
        fields = ('id', 'product', 'title', 'quantity')


class SaleSerializer(serializers.ModelSerializer):
    product_sales = ProductSaleSerializer(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = ('id', 'company', 'buyer_name', 'sale_date', 'product_sales', 'created_by', 'created_at',)
        read_only_fields = fields


class SaleCreateSerializer(serializers.Serializer):
    buyer_name = serializers.CharField(max_length=255)
    sale_date = serializers.DateField(required=False, allow_null=True)
    product_sales = ProductSaleItemSerializer(many=True)

    def validate_buyer_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Укажите имя покупателя.')
        return value

    def validate_product_sales(self, value):
        if not value:
            raise serializers.ValidationError('Укажите хотя бы один товар.')
        product_ids = [item['product'] for item in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError('Один и тот же товар указан в продаже дважды.')
        return value

    def create(self, validated_data):
        request = self.context['request']
        company = request.user.company
        items = validated_data['product_sales']
        product_ids = [item['product'] for item in items]
        sale_date = validated_data.get('sale_date') or timezone.localdate()

        with transaction.atomic():
            locked = {
                product.id: product
                for product in Product.objects.select_for_update().filter(
                    id__in=product_ids,
                    storage__company_id=company.id,
                )
            }
            missing = [product_id for product_id in product_ids if product_id not in locked]
            if missing:
                raise serializers.ValidationError(
                    {'product_sales': f'На складе компании нет товаров с id: {missing}.'}
                )

            insufficient = []
            for item in items:
                product = locked[item['product']]
                if product.quantity < item['quantity']:
                    insufficient.append(
                        f'{product.title} (есть {product.quantity}, нужно {item["quantity"]})'
                    )
            if insufficient:
                raise serializers.ValidationError(
                    {'product_sales': f'Недостаточно товара на складе: {"; ".join(insufficient)}.'}
                )

            sale = Sale.objects.create(
                company=company,
                buyer_name=validated_data['buyer_name'],
                sale_date=sale_date,
                created_by=validated_data.get('created_by') or request.user,
            )
            for item in items:
                product = locked[item['product']]
                ProductSale.objects.create(
                    sale=sale,
                    product=product,
                    quantity=item['quantity'],
                )
                product.quantity -= item['quantity']
                product.save(update_fields=['quantity'])
        return sale


class SaleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = ('buyer_name', 'sale_date')

    def validate_buyer_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Укажите имя покупателя.')
        return value

    def validate(self, attrs):
        forbidden = set(self.initial_data) - {'buyer_name', 'sale_date'}
        if forbidden:
            raise serializers.ValidationError(
                {field: 'Это поленельзя изменять.' for field in sorted(forbidden)}
            )
        return attrs
        
