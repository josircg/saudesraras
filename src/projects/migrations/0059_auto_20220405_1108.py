# Generated by Django 2.2.24 on 2022-04-05 14:08

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0058_auto_20211118_1628'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='difficultyLevel',
        ),
        migrations.RemoveField(
            model_name='project',
            name='hasTag',
        ),
        migrations.RemoveField(
            model_name='translatedproject',
            name='translatedAim',
        ),
        migrations.AddField(
            model_name='project',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='location',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
        migrations.DeleteModel(
            name='DifficultyLevel',
        ),
        migrations.DeleteModel(
            name='HasTag',
        ),
    ]
