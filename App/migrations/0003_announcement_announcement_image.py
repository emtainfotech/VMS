# Generated by Django 5.0.2 on 2025-02-10 08:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0002_employeesession_logout_reason'),
    ]

    operations = [
        migrations.AddField(
            model_name='announcement',
            name='announcement_image',
            field=models.FileField(default=0, upload_to='Announcement-image/'),
            preserve_default=False,
        ),
    ]
