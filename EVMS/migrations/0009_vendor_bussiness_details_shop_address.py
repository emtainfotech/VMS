# Generated by Django 5.0.2 on 2025-03-31 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EVMS', '0008_candidate_commission_generation_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor_bussiness_details',
            name='shop_address',
            field=models.CharField(default=0, max_length=266),
            preserve_default=False,
        ),
    ]
