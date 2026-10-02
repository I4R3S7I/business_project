from django.contrib import admin

from products.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'quantity', 'purchase_price', 'sale_price', 'storage')
    list_editable = ('quantity',)
    search_fields = ('title', 'storage__address', 'storage__company__name')
    list_select_related = ('storage', 'storage__company')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('storage',)
