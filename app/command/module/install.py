from django.conf import settings

from settings.roles import Roles
from systems.command.action import ActionCommand


class Command(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.module_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 70

    def exec(self):
        self.info("Installing module requirements...")
        self.manager.install_scripts(self, self.verbosity == 3)
        self.manager.install_requirements(self, self.verbosity == 3)

        if settings.CLI_EXEC:
            env = self.get_env()
            cid = self.manager.container_id
            image = self.manager.generate_image_name(env.base_image)

            self.manager.create_image(cid, image)
            env.runtime_image = image
            env.save()

        self.success("Successfully installed module requirements")
