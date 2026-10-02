from rest_framework import serializers

from products.models import Product


class ProductSerializer(serializers.ModelSerializer):
    purchase_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        coerce_to_string=False,
    )
    sale_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        coerce_to_string=False,
    )

    class Meta:
        model = Product
        fields = (
            'id',
            'title',
            'description',
            'quantity',
            'purchase_price',
            'sale_price',
            'storage',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'quantity', 'storage', 'created_at', 'updated_at')

    def validate(self, attrs):
        if 'quantity' in self.initial_data:
            raise serializers.ValidationError(
                {'quantity': ('Количество товара нельзя менять вручную. Можно только поставками, продажей или админкой.')}
            )
        return attrs

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Укажите название товара.')
        return value

    def _title_taken(self, storage, title):
        conflict = Product.objects.filter(storage=storage, title=title)
        if self.instance is not None:
            conflict = conflict.exclude(pk=self.instance.pk)
        return conflict.exists()

    def create(self, validated_data):
        if self._title_taken(validated_data['storage'], validated_data['title']):
            raise serializers.ValidationError({'title': 'Такой товар уже есть на складе.'})
        validated_data['quantity'] = 0
        return super().create(validated_data)

    def update(self, instance, validated_data):
        title = validated_data.get('title', instance.title)
        if self._title_taken(instance.storage, title):
            raise serializers.ValidationError({'title': 'Такой товар уже есть на складе.'})
        return super().update(instance, validated_data)
    