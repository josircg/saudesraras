# Generated by Django 3.2.23 on 2024-05-12 18:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organisations', '0011_auto_20230323_1545'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organisation',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='creator', to=settings.AUTH_USER_MODEL, verbose_name='Creator'),
        ),
    ]
