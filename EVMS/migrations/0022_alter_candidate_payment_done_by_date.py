# Generated by Django 5.1.7 on 2025-04-07 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EVMS', '0021_candidate_payment_done_by_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidate',
            name='payment_done_by_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
