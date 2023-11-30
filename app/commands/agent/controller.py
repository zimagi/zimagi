from django.conf import settings

from services.celery import app
from systems.commands.index import Agent


class Controller(Agent('controller')):

    def exec(self):
        self.notice("Running agent manager")
        self.manager.reset_spec()

        for agent in self.manager.collect_agents():
            worker = self.get_provider('worker', settings.WORKER_PROVIDER, app,
                worker_type = agent.spec.get('worker_type', 'default'),
                command_name = " ".join(agent.command),
                command_options = agent.spec.get('options', {})
            )
            if self._check_agent_schedule(agent.spec):
                worker.scale_agents(self.get_config(self.manager._get_agent_scale_config(agent.command), 0))
            else:
                worker.scale_agents(0)
