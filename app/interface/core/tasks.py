from celery import shared_task


@shared_task(bind=True, name='mcmi.command.exec')
def command_exec(self, command, **options):
    options.pop('schedule', None)
    options.pop('schedule_begin', None)
    options.pop('schedule_end', None)

    return {
        'command': command,
        'options': options,
        'messages': self.exec_command(command, options)
    }


@shared_task(bind=True, name='mcmi.schedule.clean_interval')
def clean_interval_schedule(self):
    return { 'messages': self.clean_interval_schedule() }

@shared_task(bind=True, name='mcmi.schedule.clean_crontab')
def clean_crontab_schedule(self):
    return { 'messages': self.clean_crontab_schedule() }

@shared_task(bind=True, name='mcmi.schedule.clean_datetime')
def clean_datetime_schedule(self):
    return { 'messages': self.clean_datetime_schedule() }


@shared_task(bind=True,
    name='mcmi.notification.send',
    retry_backoff = True,
    retry_backoff_max = 600,
    retry_jitter = True
)
def send_notification(self, recipient, subject, body):
    return { 'messages': self.send_notification(recipient, subject, body) }
