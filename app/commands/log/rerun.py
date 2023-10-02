from systems.commands.index import Command
from utility.data import deep_merge

import copy


class Rerun(Command('log.rerun')):

    def exec(self):
        def rerun_command(log_key):
            log = self._log.retrieve(log_key)
            if log:
                options = copy.deepcopy(deep_merge(log.config, log.secrets))
                rerun_key = self.exec_local(log.command, options)
                self.success("Task {}:{} was successfully rerun: {}".format(log.command, log_key, rerun_key))
            else:
                self.error("Log key {} does not exist".format(log_key))

        self.run_list(self.log_keys, rerun_command)
