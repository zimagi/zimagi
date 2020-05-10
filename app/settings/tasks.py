from celery import shared_task


@shared_task(bind = True, name = 'mcmi.command.exec')
def exec_command(self, command, **options):
    options.pop('schedule', None)
    options.pop('schedule_begin', None)
    options.pop('schedule_end', None)
    self.exec_command(command, options)


@shared_task(bind = True, name = 'mcmi.schedule.clean_interval')
def clean_interval_schedule(self):
    self.clean_interval_schedule()

@shared_task(bind = True, name = 'mcmi.schedule.clean_crontab')
def clean_crontab_schedule(self):
    self.clean_crontab_schedule()

@shared_task(bind = True, name = 'mcmi.schedule.clean_datetime')
def clean_datetime_schedule(self):
    self.clean_datetime_schedule()


@shared_task(bind = True,
    name = 'mcmi.notification.send',
    retry_kwargs = {'max_retries': 100},
    retry_backoff = True,
    retry_backoff_max = 600,
    retry_jitter = True
)
def send_notification(self, recipient, subject, body):
    self.send_notification(recipient, subject, body)
