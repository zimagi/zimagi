from django.conf import settings

from systems.commands.index import Command


class Install(Command('module.install')):

    def exec(self):
        self.info("Installing module requirements...")
        self.manager.install_scripts(self, self.verbosity == 3)
        self.manager.install_requirements(self, self.verbosity == 3)

        if settings.CLI_EXEC and self.manager.client:
            env = self.get_env()
            cid = self.manager.container_id
            image = self.manager.generate_image_name(env.base_image)

            old_runtime_image = self.delete_state('old_runtime_image')
            if old_runtime_image:
                self.manager.delete_image(old_runtime_image)

            self.manager.create_image(cid, image)
            self.save_env(
                runtime_image = image
            )
        self.success("Successfully installed module requirements")
