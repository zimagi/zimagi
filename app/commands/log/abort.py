from systems.commands.index import Command


class Abort(Command('log.abort')):

    def exec(self):
        def abort_command(log_key):
            self.publish_abort(log_key)
            self.wait_for_tasks(log_key)
            self.success("Task {} successfully aborted".format(log_key))

        self.run_list(self.log_names, abort_command)
