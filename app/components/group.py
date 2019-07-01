from systems.command import profile


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 1

    def run(self, name, children):
        self.exec('group children',
            group_name = name,
            group_names = [] if not children else children,
            local = self.command.local
        )

    def describe(self, instance):
        return self.get_names(instance.group_relation)

    def destroy(self, name, children):
        self.exec('group rm',
            group_name = name,
            local = self.command.local,
            force = True
        )
