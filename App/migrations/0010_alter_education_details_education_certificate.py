# Generated by Django 5.0.2 on 2025-02-12 07:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0009_alter_documents_details_employee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='education_details',
            name='education_certificate',
            field=models.FileField(blank=True, null=True, upload_to='Education-Certificate/'),
        ),
    ]
