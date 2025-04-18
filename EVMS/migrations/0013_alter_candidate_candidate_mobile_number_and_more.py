# Generated by Django 5.0.2 on 2025-03-31 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EVMS', '0012_alter_vendor_date_of_birth_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidate',
            name='candidate_mobile_number',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='candidate_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='candidate_photo',
            field=models.FileField(blank=True, null=True, upload_to='candidate-photo/'),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='candidate_resume',
            field=models.FileField(blank=True, null=True, upload_to='candidate-resume/'),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='current_working_status',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='lead_source',
            field=models.CharField(blank=True, default='EVMS', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='qualification',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='submit_by',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='unique_code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
