# Generated by Django 5.0.2 on 2025-03-31 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EVMS', '0009_vendor_bussiness_details_shop_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendor_bank_details',
            name='account_type',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
