from systems.commands.index import Command


class Scale(Command('scale')):

    def exec(self):
        agent_path = [ 'agent', *self.agent_name ]
        data = [[ 'Agent', 'Count' ]]
        found = False

        for agent in self.manager.collect_agents():
            if agent.command[:len(agent_path)] == agent_path:
                found = True
                config_name = self._get_count_config_name(agent.command)
                agent_config = self._config.retrieve(config_name)
                existing_count = agent_config.value if agent_config else 0
                count = existing_count

                if self.agent_count is not None:
                    self.save_instance(self._config, config_name, {
                            'value': self.agent_count,
                            'value_type': 'int'
                        },
                        quiet = True
                    )
                    count = "{} -> {}".format(existing_count, self.agent_count)

                data.append([
                    self.key_color(self._get_agent_name(agent.command)),
                    self.value_color(count)
                ])

        if found:
            self.table(data, 'agent-counts')
        else:
            self.warning("No agents found matching: {}".format(self._get_agent_name(agent_path)))
            exit(1)


    def _get_agent_name(self, agent_path):
        return " ".join(agent_path).removeprefix('agent').strip()

    def _get_count_config_name(self, agent_path):
        return "{}_count".format("_".join(agent_path))
