from django.db import transaction
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from companies.permissions import HasCompany
from products.models import Product
from sales.models import Sale
from sales.serializers import SaleCreateSerializer, SaleSerializer, SaleUpdateSerializer


class SalePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema_view(
    list=extend_schema(
        tags=['Продажи'],
        summary='Список продаж компании',
        parameters=[
            OpenApiParameter(
                name='date_from',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Начало периода (YYYY-MM-DD)',
                required=False,
            ),
            OpenApiParameter(
                name='date_to',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Конец периода (YYYY-MM-DD)',
                required=False,
            ),
            OpenApiParameter(
                name='page',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Номер страницы',
                required=False,
            ),
            OpenApiParameter(
                name='page_size',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Размер страницы',
                required=False,
            ),

        ],
    ),
    retrieve=extend_schema(tags=['Продажи'], summary='Продажа'),
    create=extend_schema(tags=['Продажи'], summary='Создать продажу'),
    partial_update=extend_schema(
        tags=['Продажи'],
        summary='Изменить продажу',
        description='Можно изменить только buyer_name и sale_date. Позиции продажи менять нельзя.',
    ),
    destroy=extend_schema(tags=['Продажи'], summary='Удалить продажу'),
)
class SaleViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    '''Продажи компании. Создание уменьшает остаток указанных товаров.'''

    permission_classes = [IsAuthenticated, HasCompany]
    pagination_class = SalePagination
    queryset = Sale.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        company_id = getattr(self.request.user, 'company_id', None)
        base = Sale.objects.select_related('company', 'created_by').prefetch_related(
            'product_sales__product'
        )
        if not company_id:
            return base.none()

        queryset = base.filter(company_id=company_id)
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(sale_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(sale_date__lte=date_to)
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return SaleCreateSerializer
        if self.action in ('partial_update', 'update'):
            return SaleUpdateSerializer
        return SaleSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale = serializer.save(created_by=request.user)
        sale = self.get_queryset().get(pk=sale.pk)
        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        sale = self.get_object()
        serializer = self.get_serializer(sale, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        sale = self.get_queryset().get(pk=sale.pk)
        return Response(SaleSerializer(sale).data)

    def perform_destroy(self, instance):
        with transaction.atomic():
            items = list(instance.product_sales.select_related('product'))
            product_ids = [item.product_id for item in items]
            locked = {
                product.id: product
                for product in Product.objects.select_for_update().filter(id__in=product_ids)
            }
            for item in items:
                product = locked[item.product_id]
                product.quantity += item.quantity
                product.save(update_fields=['quantity'])
            instance.delete()