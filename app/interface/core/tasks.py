from celery import shared_task

from plugins.task.base import CeleryTask


@shared_task(bind=True, base=CeleryTask, name='mcmi.task.exec')
def task_exec(self, module_name, task_name, options = None, verbosity = 2):
    if not options:
        options = {}

    self.exec_command('task', {
        'module_name': module_name,
        'task_name': task_name,
        'task_fields': options,
        'verbosity': verbosity
    })


@shared_task(bind=True, base=CeleryTask, name='mcmi.command.exec')
def command_exec(self, command):
    self.sh(command)
