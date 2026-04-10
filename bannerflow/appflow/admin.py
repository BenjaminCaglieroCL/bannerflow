from django.contrib import admin
from .models import BannerTemplate


@admin.register(BannerTemplate)
class BannerTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_predefined', 'created_at', 'updated_at')
    list_filter = ('is_predefined',)
    search_fields = ('name',)
