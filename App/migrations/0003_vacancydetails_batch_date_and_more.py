# Generated by Django 5.1.7 on 2025-07-23 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0002_company_registration_attech_proposal'),
    ]

    operations = [
        migrations.AddField(
            model_name='vacancydetails',
            name='batch_date',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='vacancydetails',
            name='cab_facility',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='vacancydetails',
            name='cab_facility_other',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='vacancydetails',
            name='incentive_details',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='vacancydetails',
            name='interview_rounds',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='vacancydetails',
            name='job_opening_origin_other',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='vacancydetails',
            name='lingual_proficiency',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='vacancydetails',
            name='maximum_salary_type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='vacancydetails',
            name='minimum_salary_type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='vacancydetails',
            name='no_of_vacancies',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='vacancydetails',
            name='working_shift',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='vacancydetails',
            name='working_shift_other',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
