# Generated by Django 4.1.2 on 2022-12-26 21:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0003_alter_scheduledtask_headers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scheduledtask',
            name='name',
            field=models.CharField(max_length=256, primary_key=True, serialize=False),
        ),
    ]
