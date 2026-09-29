from django.contrib.auth.password_validation import validate_password
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from app.users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'password_confirm', 'first_name', 'last_name')
        read_only_fields = ('id',)
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }

    def validate_email(self, value):
        return value.strip().lower()

    def validate_first_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Укажите имя пользователя.')
        return value

    def validate_last_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Укажите фамилию пользователя.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают.'})
        validate_password(attrs['password'])
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(read_only=True, allow_null=True)
    storage_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'is_company_owner', 'company_id', 'storage_id',)
        read_only_fields = fields

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_storage_id(self, obj):
        if not obj.company_id:
            return None
        return obj.company.storages.value_list('id', flat=True).first()