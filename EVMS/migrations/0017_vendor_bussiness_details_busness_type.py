# Generated by Django 5.1.7 on 2025-04-02 06:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EVMS', '0016_vendor_qr_code_plain'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor_bussiness_details',
            name='busness_type',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
