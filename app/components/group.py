from systems.commands import profile


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 1

    def run(self, name, children):
        self.exec('group children',
            group_name = name,
            group_names = [] if not children else children
        )

    def describe(self, instance):
        return self.get_names(instance.group_relation)

    def destroy(self, name, children):
        self.exec('group rm',
            group_name = name,
            force = True
        )