# Generated by Django 2.2.24 on 2023-04-18 18:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0070_auto_20230323_1545'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='external_url',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
