# Generated by Django 4.1.2 on 2022-10-28 03:12

from django.db import migrations
import systems.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0002_scheduledtask_secrets_alter_scheduledtask_args_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scheduledtask',
            name='headers',
            field=systems.models.fields.DictionaryField(default=dict),
        ),
    ]
