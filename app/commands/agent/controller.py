from django.conf import settings

from services.celery import app
from systems.commands.index import Agent


class Controller(Agent('controller')):

    def exec(self):
        def process_agents(spec, name = None, parents = None):
            if parents is None:
                parents = []
            if name and name == 'controller' and not parents:
                return

            if name and 'base' in spec:
                worker = self.get_provider('worker', settings.WORKER_PROVIDER, app,
                    worker_type = spec.get('worker_type', 'default'),
                    command_name = " ".join([ 'agent', *parents, name ]),
                    command_options = spec.get('options', {})
                )
                agent_running = worker.check_agent()

                if self._check_agent_schedule(spec):
                    if not agent_running:
                        worker.start_agent()
                elif agent_running:
                    worker.stop_agent()
            else:
                sub_parents = [ *parents, name ] if name else parents

                for key, value in spec.items():
                    if isinstance(value, dict):
                        process_agents(value, key, sub_parents)

        self.notice("Running agent manager")
        process_agents(self.manager.get_spec('command.agent'))
