# Generated by Django 5.1.7 on 2025-04-16 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0030_alter_company_registration_company_contact_person_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='termination',
            name='status',
            field=models.CharField(default='Pending', max_length=20),
        ),
    ]
