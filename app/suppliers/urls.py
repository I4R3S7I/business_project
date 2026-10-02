from django.urls import include, path
from rest_framework.routers import DefaultRouter

from suppliers.views import SupplierViewSet

router = DefaultRouter()
router.register('suppliers', SupplierViewSet, basename='supplier')

urlpatterns = [
    path('', include(router.urls)),
]