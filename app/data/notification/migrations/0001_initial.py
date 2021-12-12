# Generated by Django 3.2.5 on 2021-07-13 07:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('group', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('id', models.CharField(editable=False, max_length=64, primary_key=True, serialize=False)),
                ('name', models.CharField(editable=False, max_length=256)),
            ],
            options={
                'verbose_name': 'notification',
                'verbose_name_plural': 'notifications',
                'db_table': 'core_notification',
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NotificationGroup',
            fields=[
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('id', models.CharField(editable=False, max_length=64, primary_key=True, serialize=False)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='group.group')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='groups', to='notification.notification')),
            ],
            options={
                'verbose_name': 'notification group',
                'verbose_name_plural': 'notification groups',
                'db_table': 'core_notification_group',
                'ordering': ['id'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NotificationFailureGroup',
            fields=[
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('id', models.CharField(editable=False, max_length=64, primary_key=True, serialize=False)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='group.group')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='failure_groups', to='notification.notification')),
            ],
            options={
                'verbose_name': 'notification failure group',
                'verbose_name_plural': 'notification failure groups',
                'db_table': 'core_notification_failure_group',
                'ordering': ['id'],
                'abstract': False,
            },
        ),
    ]