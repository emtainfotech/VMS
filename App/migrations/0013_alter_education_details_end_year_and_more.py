# Generated by Django 5.0.2 on 2025-02-12 09:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0012_alter_education_details_employee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='education_details',
            name='end_year',
            field=models.CharField(blank=True, default=0, max_length=200),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='education_details',
            name='start_year',
            field=models.CharField(blank=True, default=0, max_length=200),
            preserve_default=False,
        ),
    ]
