# Generated by Django 4.0.7 on 2022-09-04 20:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0004_alter_taskcrontab_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskcrontab',
            name='name',
            field=models.CharField(editable=False, max_length=100, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='taskdatetime',
            name='name',
            field=models.CharField(editable=False, max_length=100, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='taskinterval',
            name='name',
            field=models.CharField(editable=False, max_length=100, primary_key=True, serialize=False),
        ),
    ]