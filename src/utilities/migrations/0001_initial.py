# Generated by Django 2.2.28 on 2023-06-07 17:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Translation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(choices=[('pt-br', 'Brazilian Portuguese'), ('es', 'Spanish'), ('en', 'English')], max_length=5, verbose_name='Language')),
                ('text', models.TextField(verbose_name='Translated Text')),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': 'Translation',
                'verbose_name_plural': 'Translations',
                'db_table': 'translation',
            },
        ),
        migrations.AddIndex(
            model_name='translation',
            index=models.Index(fields=['object_id', 'content_type'], name='translation_object__7d43d5_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='translation',
            unique_together={('language', 'content_type', 'object_id')},
        ),
    ]
