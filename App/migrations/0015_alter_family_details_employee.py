# Generated by Django 5.0.2 on 2025-02-12 13:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0014_alter_experience_details_employee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='family_details',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='family_member', to='App.employee'),
        ),
    ]
