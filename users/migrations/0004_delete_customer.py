# Generated by Django 5.2 on 2025-05-15 11:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healthcare', '0004_alter_patientdoctorassignment_patient'),
        ('users', '0003_remove_customer_user_patient'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Customer',
        ),
    ]
