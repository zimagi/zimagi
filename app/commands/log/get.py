from systems.commands.index import Command


class Get(Command('log.get')):

    def exec(self):
        self.table([
            [self.key_color("Log key"), self.value_color(self.log_name)],
            [self.key_color("Command"), self.value_color(self.log.command)],
            [self.key_color("Status"), self.log.status],
            [self.key_color("User"), self.log.user.name],
            [self.key_color("Scheduled"), self.log.scheduled],
            [self.key_color("Started"), self.format_time(self.log.created)],
            [self.key_color("Last Updated"), self.format_time(self.log.updated)]
        ], 'data')

        parameter_table = [[self.key_color("Parameter"), self.key_color("Value")]]
        for name, value in self.log.config.items():
            parameter_table.append([self.key_color(name), value])
        self.table(parameter_table, 'parameters')

        self.info("\nCommand Messages:\n")

        if self.log.running():
            log = self.log
            created = log.created

            while not self.disconnected:
                for record in log.messages.filter(created__gt = created).order_by('created'):
                    msg = self.create_message(record.data, decrypt = False)
                    self.info(msg.format(True))
                    created = record.created

                log = self._log.retrieve(self.log_name)
                if not log.running():
                    if log.success():
                        self.success("Command '{}' completed successfully".format(log.command))
                    else:
                        self.warning("Command '{}' completed with errors".format(log.command))
                    break

                self.sleep(self.poll_interval)
        else:
            for record in self.log.messages.all().order_by('created'):
                msg = self.create_message(record.data, decrypt = False)
                self.info(msg.format(True))
