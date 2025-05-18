from systems.commands.index import Command


class Clean(Command("log.clean")):
    def exec(self):
        self.clean_logs(log_days=self.log_days, message_days=self.log_message_days)
        self.success("Log entries successfully cleaned")
