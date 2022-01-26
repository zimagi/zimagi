from systems.commands.index import Command

import copy


class Rerun(Command('log.rerun')):

    def exec(self):
        def rerun_command(log_key):
            log = self._log.retrieve(log_key)
            if log:
                options = copy.deepcopy(log.config)
                options['push_queue'] = True

                rerun_key = self.exec_local(log.command, options)
                self.success("Task {}:{} was successfully rerun: {}".format(log.command, log_key, rerun_key))
            else:
                self.error("Log key {} does not exist".format(log_key))

        self.run_list(self.log_names, rerun_command)
