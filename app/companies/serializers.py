import re

from django.contrib.auth import get_user_model
from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import NotFound

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


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'first_name', 'last_name', 'is_company_owner')
        read_only_fields = fields


class AttachMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    email = serializers.EmailField(required=False)

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        if attrs.get('id') is None and not attrs.get('email'):
            raise serializers.ValidationError('Укажите id или email пользователя.')
        return attrs

    def create(self, validated_data):
        company = self.context['company']
        User = get_user_model()
        user_id = validated_data.get('id')
        email = validated_data.get('email')

        with transaction.atomic():
            queryset = User.objects.select_for_update()
            if user_id is not None and email:
                user = queryset.filter(pk=user_id, email=email).first()
                if user is None and (
                    User.objects.filter(pk=user_id).exists()
                    or User.objects.filter(email=email).exists()
                ):
                    raise serializers.ValidationError(
                        'id и email указывают на разных пользователей.'
                    )
            elif user_id is not None:
                user = queryset.filter(pk=user_id).first()
            else:
                user = queryset.filter(email=email).first()

            if user is None:
                raise NotFound('Пользователь не найден.')
            if user.is_company_owner:
                raise serializers.ValidationError(
                    'Владельца компании нельзя добавить в другую компанию как сотрудника.'
                )
            if user.company_id:
                raise serializers.ValidationError('Пользователь уже привязан к компании.')

            user.company = company
            user.is_company_owner = False
            user.save(update_fields=['company', 'is_company_owner'])
        return user