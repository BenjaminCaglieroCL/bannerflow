from django.db import migrations


def create_admin(apps, schema_editor):
    from django.contrib.auth.models import User
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='',
            password='admin',
        )


class Migration(migrations.Migration):

    dependencies = [
        ('appflow', '0003_remove_bannertemplate_background_image_and_more'),
    ]

    operations = [
        migrations.RunPython(create_admin, migrations.RunPython.noop),
    ]
