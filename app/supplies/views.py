from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from companies.permissions import HasCompany
from supplies.models import Supply
from supplies.serializers import SupplyCreateSerializer, SupplySerializer


def accepted_by(user):
    name = f'{user.last_name} {user.first_name}'.strip()
    return name or user.email

@extend_schema_view(
    list=extend_schema(tags=['Поставки'], summary='Список поставок'),
    retrieve=extend_schema(tags=['Поставки'], summary='Поставка'),
    create=extend_schema(tags=['Поставки'], summary='Создать поставку'),
)
class SupplyViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    '''Поставки компании. Создание увеличивает остаток указанных товаров.'''

    permission_classes = [IsAuthenticated, HasCompany]
    queryset = Supply.objects.all()
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        company_id = getattr(self.request.user, 'company_id', None)
        base = Supply.objects.select_related('supplier', 'created_by').prefetch_related('items__product')
        if not company_id:
            return base.none()
        return base.filter(supplier__company_id=company_id)

    def get_serializer_class(self):
        if self.action == 'create':
            return SupplyCreateSerializer
        return SupplySerializer

    def create(self, request, *args, **kwargs):
        payload = request.data
        if isinstance(payload, list):
            payload = {
                'supplier_id': request.query_params.get('supplier_id'),
                'delivery_date': request.query_params.get('delivery_date'),
                'products': payload,
            }
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        supply = serializer.save(created_by=request.user)
        supply = self.get_queryset().get(pk=supply.pk)
        return Response(SupplySerializer(supply).data, status=status.HTTP_201_CREATED)

    @extend_schema(tags=['Поставки'], summary='Накладная по поставке')
    @action(detail=True, methods=['get'])
    def invoice(self, request, pk=None):
        supply = self.get_object()
        return Response(
            {
                'Поставщик': supply.supplier.name,
                'ИНН': supply.supplier.inn,
                'Товары': {item.product.title: item.quantity for item in supply.items.all()},
                'Дата поставки': supply.delivery_date.isoformat(),
                'Товары принял': accepted_by(request.user),
            }
        )
