from systems.commands.index import Command


class Scale(Command('scale')):

    def exec(self):
        config_path = [ 'agent', *self.agent_name ]
        self.save_instance(self._config, "{}_count".format("_".join(config_path)), {
                'value': self.agent_count,
                'value_type': 'int'
            },
            quiet = True
        )
