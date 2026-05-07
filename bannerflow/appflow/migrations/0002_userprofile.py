import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appflow', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('awin_prefix', models.CharField(
                    blank=True,
                    default='',
                    help_text='Prefijo de afiliado Awin (Adidas). Ej: https://www.awin1.com/cread.php?awinmid=79922&awinaffid=1674245&ued=https%3A%2F%2F',
                    max_length=500,
                )),
                ('sodimac_suffix_trigger', models.CharField(
                    blank=True,
                    default='',
                    help_text='Inicio del sufijo de afiliado Sodimac. Ej: ?eid=',
                    max_length=200,
                )),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='userprofile',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]
