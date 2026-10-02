from django.db.models import ProtectedError
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from companies.permissions import HasCompany
from suppliers.models import Supplier
from suppliers.serializers import SupplierSerializer


@extend_schema_view(
    list=extend_schema(tags=['Поставщики'], summary='Список поставщиков компании.'),
    create=extend_schema(tags=['Поставщики'], summary='Создать поставщика компании.'),
    retrieve=extend_schema(tags=['Поставщики'], summary='Поставщик'),
    partial_update=extend_schema(tags=['Поставщики'], summary='Изменять поставщика'),
    destroy=extend_schema(tags=['Поставщики'], summary='Удалить поставщика'),
)
class SupplierViewSet(viewsets.ModelViewSet):
    '''Поставщики компании. Доступны владельцу и сотрудникам.'''

    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated, HasCompany]
    queryset = Supplier.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        company_id = getattr(self.request.user, 'company_id', None)
        if not company_id:
            return Supplier.objects.none()
        return Supplier.objects.filter(company_id=company_id)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

    def perform_destroy(self, instanse):
        try:
            instanse.delete()
        except ProtectedError:
            raise ValidationError('Нельзя удалить поставщика, у которого есть поставки.')