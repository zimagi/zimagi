from systems.command import profile


class Provisioner(profile.BaseProvisioner):

    def priority(self):
        return 1

    def ensure(self, name, children):
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
