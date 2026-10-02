from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from companies.models import Company
from companies.serializers import (
    CompanySerializer,
    AttachMemberSerializer,
    MemberSerializer,
    )
from companies.permissions import IsCompanyOwner, IsCompanyMember


@extend_schema(tags=['Компания'], summary='Создать компанию')
class CompanyCreateView(generics.CreateAPIView):
    '''Доступно авторизованному пользователю, у которого еще нет компании.
    Создатель становится владельцем. Вторая компания для того же пользователя не создается.
    '''

    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(tags=['Компания'], summary='Компания: просмотр, изменение, удаление')
class CompanyDetailView(generics.RetrieveUpdateDestroyAPIView):
    '''Просмотр, изменение и удаление доступны только сотруднику или владельцу этой компании.'''

    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD'):
            return [permissions.IsAuthenticated(), IsCompanyMember()]
        if self.request.method in ('PATCH', 'DELETE'):
            return [permissions.IsAuthenticated(), IsCompanyOwner()]
        return [permissions.IsAuthenticated()]

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError(
                'Нельзя удалить компанию, пока у неё есть поставки товаров.'
            )


class CompanyMemberView(APIView):
    '''Список сотрудников и прикрепление пользователя. Только для владельца компании.'''

    permission_classes = [permissions.IsAuthenticated, IsCompanyOwner]
    serializer_class = MemberSerializer

    def get_company(self, request, pk):
        company = get_object_or_404(Company, pk=pk)
        self.check_object_permissions(request, company)
        return company

    @extend_schema(
        tags=['Компании'],
        summary='Список сотрудников',
        responses=MemberSerializer(many=True),
    )
    def get(self, request, pk):
        company = self.get_company(request, pk)
        members = company.members.order_by('id')
        return Response(MemberSerializer(members, many=True).data)

    @extend_schema(
        tags=['Компании'],
        summary='Прикрепить сотрудника',
        request=AttachMemberSerializer,
        responses=MemberSerializer,
    )
    def post(self, request, pk):
        company = self.get_company(request, pk)
        serializer = AttachMemberSerializer(data=request.data, context={'company': company})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(MemberSerializer(user).data, status=status.HTTP_201_CREATED)