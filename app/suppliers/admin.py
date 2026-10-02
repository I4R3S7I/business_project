from django.contrib import admin

from suppliers.models import Supplier


@admin.register(Supplier)
class SuplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'inn', 'company', 'created_at')
    search_fields = ('name', 'inn', 'company__name')
    list_select_related = ('company',)
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('company',)
