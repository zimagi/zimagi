from systems.commands.index import Command

import sys


class Logs(Command('service.logs')):

    def exec(self):
        self.disable_logging()

        service_names = self.service_names if self.service_names else self.manager.service_names
        try:
            self.manager.display_service_logs(service_names,
                tail = self.tail,
                follow = self.follow
            )
        except KeyboardInterrupt:
            sys.exit(0)
