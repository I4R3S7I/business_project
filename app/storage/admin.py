from django.contrib import admin

from storage.models import Storage


@admin.register(Storage)
class StorageAdmin(admin.ModelAdmin):
    list_display = ('address', 'company', 'created_at')
    search_fields = ('address', 'company__name', 'company__inn')
    list_select_related = ('company',)
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('company',)
