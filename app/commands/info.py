from systems.commands.index import Command


class Info(Command("info")):
    def exec(self):
        self.notice("Platform Information")
        self.table(
            [
                [self.key_color("Version"), self.value_color(self.get_version())],
            ],
            "platform_info",
        )
        self.info("")

        if self._host.count():
            self.notice("Remote Hosts")
            self.table(self.render_list(self._host), "hosts")
            self.info("")

        self.notice("Installed Modules")
        self.table(self.render_list(self._module), "modules")
        self.info("")
