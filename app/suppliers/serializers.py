import re

from rest_framework import serializers

from suppliers.models import Supplier

INN_PATTERN = re.compile(r'^\d{10}$|^\d{12}$')


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ('id', 'company', 'name', 'inn', 'created_at', 'updated_at')
        read_only_fields = ('id', 'company', 'created_at', 'updated_at')

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Укажите название поставщика.')
        return value

    def validate_inn(self, value):
        value = value.strip()
        if not INN_PATTERN.fullmatch(value):
            raise serializers.ValidationError('ИНН должен содержать 10 или 12 цифр.')
        return value

    def validate(self, attrs):
        inn = attrs.get('inn')
        if inn is None and self.instance is not None:
            inn = self.instance.inn
        company_id = self.context['request'].user.company_id
        conflict = Supplier.objects.filter(company_id=company_id, inn=inn)
        if self.instance is not None:
            conflict = conflict.exclude(pk=self.instance.pk)
        if inn and conflict.exists():
            raise serializers.ValidationError(
                {'inn': 'У компании уже есть поставщик с таким ИНН.'}
            )
        return attrs
    