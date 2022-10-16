from celery import shared_task


@shared_task(bind = True,
    name = 'zimagi.command.exec',
    autoretry_for = (Exception,),
    retry_backoff = True,
    retry_backoff_max = (5 * 60),
    retry_jitter = True
)
def exec_command(self, command, **options):
    options.pop('schedule', None)
    options.pop('schedule_begin', None)
    options.pop('schedule_end', None)
    options.pop('push_queue', None)
    options.pop('async_exec', None)
    self.exec_command(command, options)


@shared_task(bind = True, name = 'zimagi.schedule.clean_interval')
def clean_interval_schedule(self):
    self.clean_interval_schedule()

@shared_task(bind = True, name = 'zimagi.schedule.clean_crontab')
def clean_crontab_schedule(self):
    self.clean_crontab_schedule()

@shared_task(bind = True, name = 'zimagi.schedule.clean_datetime')
def clean_datetime_schedule(self):
    self.clean_datetime_schedule()


@shared_task(bind = True,
    name = 'zimagi.notification.send',
    autoretry_for = (Exception,),
    retry_kwargs = { 'max_retries': 25 },
    retry_backoff = True,
    retry_backoff_max = (5 * 60),
    retry_jitter = True
)
def send_notification(self, recipient, subject, body):
    self.send_notification(recipient, subject, body)
