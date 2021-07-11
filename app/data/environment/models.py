from systems.models.index import Model, ModelFacade
from utility.runtime import Runtime


class EnvironmentFacade(ModelFacade('environment')):

    def ensure(self, command, reinit):
        env_name = self.get_env()
        env = self.retrieve(env_name)

        if not env:
            env = command.environment_provider.create(env_name, {})

        if not Runtime.data:
            env.runtime_image = None
            env.save()

    def delete(self, key, **filters):
        return True


    def get_env(self):
        return Runtime.get_env()

    def set_env(self, name = None, repo = None, image = None):
        Runtime.set_env(name, repo, image)

    def delete_env(self):
        Runtime.delete_env()


class Environment(Model('environment')):

    def save(self, *args, **kwargs):
        env_name = Runtime.get_env()
        if self.name == env_name:
            image = self.base_image
            if self.runtime_image:
                image = self.runtime_image

            Runtime.set_env(
                self.name,
                self.repo,
                image
        )
        super().save(*args, **kwargs)
