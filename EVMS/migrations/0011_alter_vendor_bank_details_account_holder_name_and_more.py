# Generated by Django 5.0.2 on 2025-03-31 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EVMS', '0010_alter_vendor_bank_details_account_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendor_bank_details',
            name='account_holder_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='vendor_bank_details',
            name='account_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='vendor_bank_details',
            name='bank_name',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='vendor_bank_details',
            name='ifs_code',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='vendor_bank_details',
            name='micr_code',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='vendor_bank_details',
            name='preffered_payout_date',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
