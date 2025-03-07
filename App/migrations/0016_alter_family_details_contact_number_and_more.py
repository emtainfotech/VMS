# Generated by Django 5.0.2 on 2025-02-12 13:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0015_alter_family_details_employee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='family_details',
            name='contact_number',
            field=models.CharField(blank=True, default=0, max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='family_details',
            name='date_of_birth',
            field=models.CharField(blank=True, default=0, max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='family_details',
            name='member_name',
            field=models.CharField(blank=True, default=0, max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='family_details',
            name='relation',
            field=models.CharField(blank=True, default=0, max_length=100),
            preserve_default=False,
        ),
    ]
