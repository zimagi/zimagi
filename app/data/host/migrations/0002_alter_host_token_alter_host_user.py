# Generated by Django 4.1.13 on 2025-05-15 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("host", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="host",
            name="token",
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name="host",
            name="user",
            field=models.CharField(max_length=150, null=True),
        ),
    ]
