from systems.commands.index import Command

import sys


class Logs(Command('service.logs')):

    def exec(self):
        self.disable_logging()
        try:
            self.manager.display_service_logs(self.service_names,
                tail = self.tail,
                follow = self.follow
            )
        except KeyboardInterrupt:
            sys.exit(0)
