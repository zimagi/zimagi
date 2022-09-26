# Generated by Django 4.0.7 on 2022-09-26 08:38

from django.db import migrations, models
import systems.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0005_alter_group_config_alter_group_name_and_more'),
        ('dataset', '0004_alter_dataset_config_alter_dataset_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='config',
            field=systems.models.fields.DictionaryField(default=dict),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='groups',
            field=models.ManyToManyField(blank=True, related_name='%(data_name)s', to='group.group'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='name',
            field=models.CharField(max_length=100, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='provider_type',
            field=models.CharField(default='base', max_length=128),
        ),
    ]
