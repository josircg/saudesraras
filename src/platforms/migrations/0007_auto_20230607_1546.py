# Generated by Django 2.2.28 on 2023-06-07 18:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('platforms', '0006_auto_20220727_0958'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeographicExtend',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=40, unique=True, verbose_name='Description')),
            ],
            options={
                'verbose_name': 'Geographic Extend',
                'verbose_name_plural': 'Geographics Extends',
            },
        ),
        migrations.AddField(
            model_name='platform',
            name='geoExtend',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='platforms.GeographicExtend'),
        ),
    ]
