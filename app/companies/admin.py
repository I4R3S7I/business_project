from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import OuterRef, Subquery

from companies.models import Company
from storage.models import Storage


class StorageInLine(admin.StackedInline):
    model = Storage
    extra = 0
    max_num = 1


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'inn', 'owner_email', 'created_at')
    search_fields = ('name', 'inn')
    readonly_fields = ('created_at', 'updated_at')
    inlines = (StorageInLine, )

    def get_queryset(self, request):
        User = get_user_model()
        owner_email = User.objects.filter(
            company=OuterRef('pk'),
            is_company_owner=True,
        ).values('email')[:1]
        return super().get_queryset(request).annotate(_owner_email=Subquery(owner_email))


    @admin.display(description='владелец', ordering='_owner_email')
    def owner_email(self, obj):
        return obj._owner_email or '-'
