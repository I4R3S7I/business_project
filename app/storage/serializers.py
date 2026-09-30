from rest_framework import serializers

from storage.models import Storage


class StorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Storage
        fields = ('id', 'company', 'address', 'created_at', 'updated_at')
        read_only_fields = ('id', 'company', 'created_at', 'updated_at')

    def validate_address(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Укажите адрес склада.')
        return value