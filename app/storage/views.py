from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError

from companies.permissions import IsCompanyOwner, IsCompanyMember, IsCurrentCompanyOwner
from storage.models import Storage
from storage.serializers import StorageSerializer


@extend_schema(tags=['Склады'], summary='Создать склад компании')
class StorageCreateView(generics.CreateAPIView):
    '''Склад создает владелец компании. У компании может быть только оин склад.'''

    serializer_class = StorageSerializer
    permission_classes = [permissions.IsAuthenticated, IsCurrentCompanyOwner]

    def perform_create(self, serializer):
        company = self.request.user.company
        if Storage.objects.filter(company=company).exists():
            raise ValidationError('У компании уже есть склад.')
        serializer.save(company=company)


@extend_schema(tags=['Склады'], summary='Склад: просмотр, изменение, удаление')
class StorageDetailView(generics.RetrieveUpdateDestroyAPIView):
    '''Просмотр доступен всем пользователям компании, за которой закреплен склад.
    Изменение и удаление доступны только владельцу этой компании.'''

    queryset = Storage.objects.select_related('company')
    serializer_class = StorageSerializer
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD'):
            return [permissions.IsAuthenticated(), IsCompanyMember()]
        return [permissions.IsAuthenticated(), IsCompanyOwner()]
