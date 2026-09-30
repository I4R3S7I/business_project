import re

from django.contrib.auth import get_user_model
from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from companies.models import Company

INN_PATTERN = re.compile(r'^\d{10}$|^\d{12}$')


class CompanySerializer(serializers.ModelSerializer):
    owner_id = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ('id', 'name', 'inn', 'description',  'owner_id', 'owner_email', 'created_at', 'updated_at',)
        read_only_fields = ('id', 'owner_id', 'owner_email', 'created_at', 'updated_at',)

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Укажите название компании.')
        return value

    def validate_inn(self, value):
        value = value.strip()
        if not INN_PATTERN.fullmatch(value):
            raise serializers.ValidationError('ИНН должен содержать 10 или 12 цифр.')
        return value

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_owner_id(self, obj):
        owner = obj.get_owner()
        return owner.id if owner else None

    @extend_schema_field(serializers.EmailField(allow_null=True))
    def get_owner_email(self, obj):
        owner = obj.get_owner()
        return owner.email if owner else None

    def create(self, validated_data):
        user = self.context['request'].user
        User = get_user_model()
        with transaction.atomic():
            locked = User.objects.select_for_update().get(pk=user.pk)
            if locked.company_id or locked.is_company_owner:
                raise serializers.ValidationError(
                    'Пользователь может создать только одну компанию и может быть связан только с одной компанией.'
                )
            company = Company.objects.create(**validated_data)
            locked.company = company
            locked.is_company_owner = True
            locked.save(update_fields=['company', 'is_company_owner'])
        return company