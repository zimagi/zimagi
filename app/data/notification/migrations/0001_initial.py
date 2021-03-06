# Generated by Django 3.0 on 2020-02-02 09:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('group', '0001_initial'),
        ('environment', '0002_auto_20190520_0649'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('id', models.CharField(editable=False, max_length=64, primary_key=True, serialize=False)),
                ('name', models.CharField(editable=False, max_length=256)),
                ('environment', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='notification_relation', to='environment.Environment')),
            ],
            options={
                'verbose_name': 'notification',
                'verbose_name_plural': 'notifications',
                'db_table': 'core_notification',
            },
        ),
        migrations.CreateModel(
            name='NotificationSuccessGroup',
            fields=[
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('id', models.CharField(editable=False, max_length=64, primary_key=True, serialize=False)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='group.Group')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='success_groups', to='notification.Notification')),
            ],
            options={
                'verbose_name': 'notification success group',
                'verbose_name_plural': 'notification success groups',
                'db_table': 'core_notification_success_group',
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='NotificationFailureGroup',
            fields=[
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('id', models.CharField(editable=False, max_length=64, primary_key=True, serialize=False)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='group.Group')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='failure_groups', to='notification.Notification')),
            ],
            options={
                'verbose_name': 'notification failure group',
                'verbose_name_plural': 'notification failure groups',
                'db_table': 'core_notification_failure_group',
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='NotificationAllGroup',
            fields=[
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('id', models.CharField(editable=False, max_length=64, primary_key=True, serialize=False)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='group.Group')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='all_groups', to='notification.Notification')),
            ],
            options={
                'verbose_name': 'notification group',
                'verbose_name_plural': 'notification groups',
                'db_table': 'core_notification_all_group',
                'ordering': ('id',),
            },
        ),
    ]
