# Generated by Django 2.2.13 on 2021-10-26 00:21

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organisations', '0006_auto_20210311_1231'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisation',
            name='location',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='contactPointEmail',
            field=models.EmailField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='url',
            field=models.URLField(),
        ),
    ]
