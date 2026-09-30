from rest_framework.permissions import BasePermission

from companies.models import Company


def related_company_id(obj):
    if isinstance(obj, Company):
        return obj.pk
    return obj.company_id


class IsCurrentCompanyOwner(BasePermission):
    '''Текущий пользователь - владелец своей компании.'''

    message = 'Действие доступно владельцу компании.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and user.is_company_owner and user.company_id)


class IsCompanyOwner(BasePermission):
    '''Объект принадлежит компании, которой владеет текущий пользвователь.'''

    message = 'Действие доступно только владельцу компании.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(
            user.is_authenticated
            and user.is_company_owner
            and user.company_id
            and user.company_id == related_company_id(obj)
        )


class IsCompanyMember(BasePermission):
    '''Текущий пользователь привязан к компании объекта.'''

    message = 'Действие доступно только пользователям этой компании.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(
            user.is_authenticated
            and user.company_id
            and user.company_id == related_company_id(obj)
        )