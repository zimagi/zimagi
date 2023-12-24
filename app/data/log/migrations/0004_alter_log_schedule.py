# Generated by Django 4.1.10 on 2023-11-30 19:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0004_alter_scheduledtask_name'),
        ('log', '0003_alter_log_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='schedule',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(data_name)s', to='schedule.scheduledtask'),
        ),
    ]