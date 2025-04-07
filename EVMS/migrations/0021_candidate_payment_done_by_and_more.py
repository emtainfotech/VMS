# Generated by Django 5.1.7 on 2025-04-07 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('EVMS', '0020_candidate_admin_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='payment_done_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='candidate',
            name='payment_done_by_date',
            field=models.DateField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='candidate',
            name='submit_recipt',
            field=models.FileField(blank=True, null=True, upload_to='vendor-payout-recipt/'),
        ),
    ]
