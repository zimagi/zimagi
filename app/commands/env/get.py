from systems.commands.index import Command


class Get(Command('env.get')):

    def exec(self):
        env_name = self.environment_name if self.environment_name else self.curr_env_name
        env = self.get_env(env_name)

        self.notice("Environment Information")
        self.table([
            [self.key_color("Name"), self.value_color(env.name)],
            [self.key_color("Image Repository"), self.value_color(str(env.repo))],
            [self.key_color("Base Image"), self.value_color(str(env.base_image))],
            [self.key_color("Runtime Image"), self.value_color(str(env.runtime_image))],
            [self.key_color("Version"), self.value_color(self.get_version())],
            [self.key_color("Created"), self.value_color(self.format_time(env.created))],
            [self.key_color("Updated"), self.value_color(self.format_time(env.updated))]
        ], 'environment_info')
        self.info('')

        if self._host.count():
            self.notice("Remote Hosts")
            self.table(self.render_list(self._host), 'hosts')
            self.info('')

        self.notice("Installed Modules")
        self.table(self.render_list(self._module), 'modules')
        self.info('')
