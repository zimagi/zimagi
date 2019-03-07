from systems.command import types, mixins
from utility import parallel

import time
import random


class Command(
    types.EnvironmentActionCommand
):
    def get_command_name(self):
        return 'test'

    def exec(self):
        def process(value):
            time.sleep(random.randint(0,5))
            value = value * 2
            self.info(str(value * 2))

            if value == 20:
                self.error("Value must not be 20")
            return value

        result = self.run_list(range(20), process)
        self.data('results', str(result.data))
        self.data('errors', str(result.errors))

