# Generated by Django 5.0.2 on 2025-03-27 09:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0024_alter_candidate_registration_next_follow_up_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidate_registration',
            name='candidate_joining_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='candidate_registration',
            name='selection_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
