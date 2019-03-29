from systems.command import profile


class Provisioner(profile.BaseProvisioner):

    def priority(self):
        return 1

    def ensure(self, name, children):
        self.command.exec_local('group children', {
            'group_name': name,
            'group_names': [] if not children else children
        })

    def describe(self, instance):
        return [ x.name for x in instance.group_relation.all() ]

    def destroy(self, name, children):
        self.command.exec_local('group rm', {
            'group_name': name,
            'force': True
        })
