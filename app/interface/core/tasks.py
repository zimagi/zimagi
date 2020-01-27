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
