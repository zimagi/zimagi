import copy

from systems.commands.index import Command
from utility.data import deep_merge


class Rerun(Command("log.rerun")):
    def exec(self):
        def rerun_command(log_key):
            log = self._log.retrieve(log_key)
            if log:
                options = copy.deepcopy(deep_merge(log.config, log.secrets))
                rerun_key = self.exec_local(log.command, options)
                self.success(f"Task {log.command}:{log_key} was successfully rerun: {rerun_key}")
            else:
                self.error(f"Log key {log_key} does not exist")

        self.run_list(self.log_keys, rerun_command)
