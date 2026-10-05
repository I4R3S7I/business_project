from django.db.models import ProtectedError
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from companies.permissions import HasCompany
from products.models import Product
from products.serializers import ProductSerializer


@extend_schema_view(
    list=extend_schema(tags=['Товары'], summary='Список товаров компании'),
    create=extend_schema(tags=['Товары'], summary='Добавить товар'),
    retrieve=extend_schema(tags=['Товары'], summary='Товар'),
    partial_update=extend_schema(tags=['Товары'], summary='Изменить товар'),
    destroy=extend_schema(tags=['Товары'], summary='Удалить товар'),
)
class ProductViewSet(viewsets.ModelViewSet):
    '''Товары склада компании. Доступны владельцу и сотрудникам.
    При создании quantity всегда 0. Пополнение идет через поставку.'''

    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, HasCompany]
    queryset = Product.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        company_id = getattr(self.request.user, 'company_id', None)
        if not company_id:
            return Product.objects.none()
        return Product.objects.filter(storage__company_id=company_id)

    def perform_create(self, serializer):
        storage = self.request.user.company.storages.first()
        if storage is None:
            raise ValidationError('Сначала создайте склад компании.')
        serializer.save(storage=storage, quantity=0)

    def perform_destroy(self, instance):
        if instance.quantity:
            raise ValidationError(
                'Нельзя удалить товар, пока его количество на складе больше нуля.'
            )
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError('Нельзя удалить товар, который уже есть в поставках или продажах.')