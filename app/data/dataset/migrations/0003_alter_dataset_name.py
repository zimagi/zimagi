# Generated by Django 4.1.2 on 2022-12-26 21:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset', '0002_alter_dataset_secrets'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='name',
            field=models.CharField(max_length=256, primary_key=True, serialize=False),
        ),
    ]