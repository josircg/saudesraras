# Generated by Django 2.2.24 on 2022-06-07 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0046_auto_20220419_0930'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='inLanguage',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
