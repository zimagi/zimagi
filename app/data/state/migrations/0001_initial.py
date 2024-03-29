# Generated by Django 4.1.2 on 2022-10-26 05:51

from django.db import migrations, models
import systems.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='State',
            fields=[
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('name', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('value', systems.models.fields.EncryptedDataField(null=True)),
            ],
            options={
                'verbose_name': 'state',
                'verbose_name_plural': 'states',
                'db_table': 'core_state',
                'ordering': ['name'],
                'abstract': False,
            },
        ),
    ]
