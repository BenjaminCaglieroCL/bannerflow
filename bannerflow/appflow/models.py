from django.db import models
from django.contrib.auth.models import User
import json


class BannerTemplate(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='templates',
    )
    name = models.CharField(max_length=200)
    canvas_data = models.JSONField(
        default=dict,
        help_text="Fabric.js canvas JSON data"
    )
    thumbnail = models.ImageField(
        upload_to='thumbnails/',
        blank=True,
        null=True
    )
    is_predefined = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name
