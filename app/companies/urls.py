from django.urls import path

from companies.views import CompanyCreateView, CompanyDetailView, CompanyMemberView

urlpatterns = [
    path('companies/', CompanyCreateView.as_view(), name='company-create'),
    path('companies/<int:pk>/', CompanyDetailView.as_view(), name='company-detail'),
    path('companies/<int:pk>/members/', CompanyMemberView.as_view(), name='company-members'),
]