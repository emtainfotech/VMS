# Generated by Django 5.1.7 on 2025-06-24 12:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0013_candidate_registration_job_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='company_registration',
            name='company_status',
            field=models.CharField(blank=True, default='Pending', max_length=100, null=True),
        ),
    ]
