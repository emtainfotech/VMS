# Generated by Django 5.0.2 on 2025-03-29 10:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EVMS', '0006_alter_candidate_vendor_payout_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidate',
            name='selection_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='vendor_commission',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
