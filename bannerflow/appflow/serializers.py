from rest_framework import serializers
from .models import BannerTemplate


class BannerTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BannerTemplate
        fields = ['id', 'name', 'canvas_data', 'is_predefined', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
