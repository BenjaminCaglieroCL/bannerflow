# Generated manually for multi-format support

from django.db import migrations, models


def convert_legacy_canvas_data(apps, schema_editor):
    """Convert existing single canvas_data to multi-format structure"""
    BannerTemplate = apps.get_model('appflow', 'BannerTemplate')
    
    for template in BannerTemplate.objects.all():
        if template.canvas_data and not isinstance(template.canvas_data, dict) or (
            isinstance(template.canvas_data, dict) and 
            not any(key in template.canvas_data for key in ['1:1', '4:5', '1.91:1', '9:16'])
        ):
            # Convert legacy format to multi-format
            legacy_data = template.canvas_data or {}
            template.canvas_data = {
                '1:1': legacy_data,      # Default format
                '4:5': legacy_data,      # Copy to vertical
                '1.91:1': legacy_data,   # Copy to horizontal 
                '9:16': legacy_data      # Copy to stories
            }
            template.save()


def reverse_conversion(apps, schema_editor):
    """Revert to legacy single canvas_data (use 1:1 format)"""
    BannerTemplate = apps.get_model('appflow', 'BannerTemplate')
    
    for template in BannerTemplate.objects.all():
        if isinstance(template.canvas_data, dict) and '1:1' in template.canvas_data:
            template.canvas_data = template.canvas_data['1:1']
            template.save()


class Migration(migrations.Migration):

    dependencies = [
        ('appflow', '0001_initial'),
    ]

    operations = [
        # Add background_image field
        migrations.AddField(
            model_name='bannertemplate',
            name='background_image',
            field=models.ImageField(blank=True, help_text='Custom background image for template', null=True, upload_to='backgrounds/'),
        ),
        # Update canvas_data help text
        migrations.AlterField(
            model_name='bannertemplate',
            name='canvas_data',
            field=models.JSONField(default=dict, help_text='Multi-format Fabric.js canvas JSON data by format ratio'),
        ),
        # Run data migration
        migrations.RunPython(convert_legacy_canvas_data, reverse_conversion),
    ]