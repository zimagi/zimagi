from systems.commands.index import Command


class List(Command("env.list")):
    def exec(self):
        records = [
            [
                self.key_color("Name"),
                self.key_color("Image Repository"),
                self.key_color("Base Image"),
                self.key_color("Runtime Image"),
                self.key_color("Created"),
                self.key_color("Updated"),
            ]
        ]
        for name, env in self.get_all_env().items():
            records.append(
                [
                    self.value_color(env.name),
                    self.value_color(str(env.repo)),
                    self.value_color(str(env.base_image)),
                    self.value_color(str(env.runtime_image)),
                    self.value_color(self.format_time(env.created)),
                    self.value_color(self.format_time(env.updated)),
                ]
            )
        self.table(records, "environment_info")
        self.spacing()
