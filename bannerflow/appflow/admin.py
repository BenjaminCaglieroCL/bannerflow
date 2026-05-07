from django.contrib import admin
from .models import BannerTemplate, UserProfile


@admin.register(BannerTemplate)
class BannerTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_predefined', 'created_at', 'updated_at')
    list_filter = ('is_predefined',)
    search_fields = ('name',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'awin_prefix', 'sodimac_suffix_trigger')
    search_fields = ('user__username',)
