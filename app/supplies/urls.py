from django.urls import path, include
from rest_framework.routers import DefaultRouter

from supplies.views import SupplyViewSet

router = DefaultRouter()
router.register('supplies', SupplyViewSet, basename='supply')

urlpatterns = [
    path('', include(router.urls)),
]