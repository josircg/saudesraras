# Generated by Django 2.2.24 on 2022-11-05 21:56

from django.db import migrations, models


def unhide_all(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    Project.objects.all().update(hidden=False)


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0067_merge_20221105_1614'),
    ]

    operations = [
        migrations.RunPython(unhide_all),
        migrations.AlterField(
            model_name='project',
            name='hidden',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]

