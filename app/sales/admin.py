from django.contrib import admin

from sales.models import ProductSale, Sale


class ProductSaleInline(admin.TabularInline):
    model = ProductSale
    extra = 0
    autocomplete_fields = ('product',)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer_name', 'company', 'sale_date', 'created_by', 'created_at')
    list_select_related = ('company', 'created_by')
    search_fields = ('buyer_name', 'company__name')
    list_filter = ('sale_date', 'company')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('company', 'created_by')
    inlines = (ProductSaleInline,)


@admin.register(ProductSale)
class ProductSaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'sale', 'product', 'quantity')
    list_select_related = ('sale', 'product')
    search_fields = ('product__title', 'sale__buyer_name')
    autocomplete_fields = ('sale', 'product')
    
