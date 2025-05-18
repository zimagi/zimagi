from systems.commands.index import Command


class Abort(Command("log.abort")):
    def exec(self):
        def abort_command(log_key):
            self.publish_abort(log_key)
            self.wait_for_tasks(log_key)
            self.success(f"Task {log_key} successfully aborted")

        self.run_list(self.log_keys, abort_command)
