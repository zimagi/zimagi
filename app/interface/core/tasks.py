from celery import shared_task

import sys
import io


@shared_task(bind=True, name='mcmi.task.exec')
def task_exec(self, module_name, task_name, task_fields = None, verbosity = 2):
    if not task_fields:
        task_fields = {}

    task_options = {
        'module_name': module_name,
        'task_name': task_name,
        'task_fields': task_fields,
        'verbosity': verbosity
    }

    old_stdout = sys.stdout
    sys.stdout = mystdout = io.StringIO()

    self.exec_command('task', task_options)

    sys.stdout = old_stdout

    task_options['messages'] = mystdout.getvalue()
    return task_options


@shared_task(bind=True, name='mcmi.command.exec')
def command_exec(self, command, **options):
    options.pop('schedule', None)
    options.pop('schedule_begin', None)
    options.pop('schedule_end', None)

    old_stdout = sys.stdout
    sys.stdout = mystdout = io.StringIO()

    self.exec_command(command, options)

    sys.stdout = old_stdout
    return {
        'command': command,
        'options': options,
        'messages': mystdout.getvalue()
    }
