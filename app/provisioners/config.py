from systems.command import profile


class Provisioner(profile.BaseProvisioner):

    def priority(self):
        return 0
