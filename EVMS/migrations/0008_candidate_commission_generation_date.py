# Generated by Django 5.0.2 on 2025-03-29 10:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EVMS', '0007_alter_candidate_selection_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='commission_generation_date',
            field=models.DateField(blank=True, default=None, null=True),
        ),
    ]
