from django.db import models
from django.contrib.auth.models import User
import json


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='userprofile',
    )
    # Awin affiliate prefix (Adidas). Example:
    # https://www.awin1.com/cread.php?awinmid=79922&awinaffid=1674245&ued=https%3A%2F%2F
    awin_prefix = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text=(
            'Prefijo de afiliado Awin (Adidas). '
            'Ej: https://www.awin1.com/cread.php?awinmid=79922&awinaffid=1674245&ued=https%3A%2F%2F'
        ),
    )
    # Sodimac affiliate suffix trigger. Example: ?eid=
    sodimac_suffix_trigger = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text='Inicio del sufijo de afiliado Sodimac. Ej: ?eid=',
    )

    def __str__(self):
        return f'Perfil de {self.user.username}'


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


class GeneratedBanner(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='generated_banners',
    )
    template = models.ForeignKey(
        BannerTemplate,
        on_delete=models.SET_NULL,
        related_name='generated_banners',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=300, blank=True, default='')
    store_name = models.CharField(max_length=120, blank=True, default='')
    offer_price = models.CharField(max_length=80, blank=True, default='')
    source_url = models.URLField(blank=True, default='')
    ratio = models.CharField(max_length=20, default='1:1')
    image = models.ImageField(upload_to='generated_banners/%Y/%m/%d/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        base = self.title or 'Banner sin titulo'
        return f'{base} ({self.owner.username})'
