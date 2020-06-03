from settings.config import Config
from systems.command.index import Command


class Start(Command('db.start')):

    def exec(self):
        self.manager.start_service(self, 'zimagi-postgres',
            "postgres:12", { 5432: None },
            environment = {
                'POSTGRES_USER': Config.string('ZIMAGI_POSTGRES_USER', 'zimagi'),
                'POSTGRES_PASSWORD': Config.string('ZIMAGI_POSTGRES_PASSWORD', 'zimagi'),
                'POSTGRES_DB': Config.string('ZIMAGI_POSTGRES_DB', 'zimagi')
            },
            volumes = {
                'zimagi-postgres': {
                    'bind': '/var/lib/postgresql',
                    'mode': 'rw'
                }
            },
            memory = self.memory,
            wait = 20
        )
        self.success('Successfully started PostgreSQL database service')
