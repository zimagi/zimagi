from systems.commands.index import Command

import yaml


class Get(Command('log.get')):

    def exec(self):
        self.table([
            [self.key_color("Log key"), self.value_color(self.log_key)],
            [self.key_color("Command"), self.value_color(self.log.command)],
            [self.key_color("Status"), self.log.status],
            [self.key_color("User"), self.relation_color(self.log.user.name)],
            [self.key_color("Schedule"), self.relation_color(self.log.schedule.name) if self.log.schedule else None],
            [self.key_color("Worker"), self.log.worker],
            [self.key_color("Started"), self.format_time(self.log.created)],
            [self.key_color("Last Updated"), self.format_time(self.log.updated)]
        ], 'data')

        parameter_table = [[self.key_color("Parameter"), self.key_color("Value")]]
        for name, value in self.log.config.items():
            if isinstance(value, (list, tuple, dict)):
                value = yaml.dump(value)
            else:
                value = str(value)

            parameter_table.append([self.key_color(name), value])
        self.table(parameter_table, 'parameters')

        secrets_table = [[self.key_color("Secret"), self.key_color("Value")]]
        for name, value in self.log.secrets.items():
            if isinstance(value, (list, tuple, dict)):
                value = yaml.dump(value)
            else:
                value = str(value)

            secrets_table.append([self.key_color(name), self.encrypted_color(value)])
        self.table(secrets_table, 'secrets')

        if self.log.schedule:
            self.info("\nSchedule Information:")
            self.table(self.render_display(
                    self.log.schedule.facade,
                    self.log.schedule
                ),
                'schedule',
                row_labels = True
            )

        self.info("\nCommand Messages:\n")

        if self.log.running():
            log = self.log
            created = log.created

            while self.connected():
                for record in log.messages.filter(created__gt = created).order_by('created'):
                    self.message(self.create_message(record.data, decrypt = False), log = False)
                    created = record.created

                log = self._log.retrieve(self.log_key)
                if not log.running():
                    if log.success():
                        self.success("Command '{}' completed successfully".format(log.command))
                    else:
                        self.warning("Command '{}' completed with errors".format(log.command))
                    break

                self.sleep(self.poll_interval)
        else:
            for record in self.log.messages.all().order_by('created'):
                self.message(self.create_message(record.data, decrypt = False), log = False)
