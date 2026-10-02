from django.contrib import admin

from supplies.models import Supply, SupplyProduct


class SupplyProductInline(admin.TabularInline):
    model = SupplyProduct
    extra = 0
    autocomplete_fields = ('product',)


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'delivery_date', 'created_by', 'created_at')
    list_select_related = ('supplier', 'created_by')
    search_fields = ('supplier__name', 'supplier__inn')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('supplier', 'created_by')
    inlines = (SupplyProductInline,)