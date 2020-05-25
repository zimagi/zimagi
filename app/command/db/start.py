from settings.config import Config
from systems.command.index import Command


class Action(Command('db.start')):

    def exec(self):
        self.manager.start_service(self, 'mcmi-postgres',
            "postgres:12", { 5432: None },
            environment = {
                'POSTGRES_USER': Config.string('MCMI_POSTGRES_USER', 'mcmi'),
                'POSTGRES_PASSWORD': Config.string('MCMI_POSTGRES_PASSWORD', 'mcmi'),
                'POSTGRES_DB': Config.string('MCMI_POSTGRES_DB', 'mcmi')
            },
            volumes = {
                'mcmi-postgres': {
                    'bind': '/var/lib/postgresql',
                    'mode': 'rw'
                }
            },
            memory = self.memory,
            wait = 20
        )
        self.success('Successfully started PostgreSQL database service')
