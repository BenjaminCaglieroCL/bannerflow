from django.contrib import admin
from .models import BannerTemplate, UserProfile, GeneratedBanner


@admin.register(BannerTemplate)
class BannerTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_predefined', 'created_at', 'updated_at')
    list_filter = ('is_predefined',)
    search_fields = ('name',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'awin_prefix', 'sodimac_suffix_trigger')
    search_fields = ('user__username',)


@admin.register(GeneratedBanner)
class GeneratedBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'store_name', 'owner', 'ratio', 'created_at')
    list_filter = ('store_name', 'ratio', 'created_at')
    search_fields = ('title', 'store_name', 'owner__username')
