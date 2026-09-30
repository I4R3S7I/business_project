from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions

from companies.models import Company
from companies.serializers import CompanySerializer
from companies.permissions import IsCompanyOwner


@extend_schema(tags=['Компания'], summary='Создать компанию')
class CompanyCreateView(generics.CreateAPIView):
    '''Доступно авторизованному пользователю, у которого еще нет компании.
    Создатель становится владельцем. Вторая компания для того же пользователя не создается.
    '''

    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(tags=['Компания'], summary='Компания: просмотр, изменение, удаление')
class CompanyDetailView(generics.RetrieveUpdateDestroyAPIView):
    '''Просмотр доступен любому авторизованному пользователю.
    Изменение и удаление доступны только владельцу этой компании.
    '''

    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.request.method in ('PATCH', 'DELETE'):
            return [permissions.IsAuthenticated(), IsCompanyOwner()]
        return [permissions.IsAuthenticated()]
    