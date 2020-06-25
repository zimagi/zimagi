from django.conf import settings

from systems.commands.index import CommandMixin


class EnvironmentMixin(CommandMixin('environment')):

    @property
    def curr_env_name(self):
        return self._environment.get_env()


    def get_env(self, host_name = None):
        name = self._environment.get_env()
        env = self.get_instance(self._environment, name, required = False)
        host = None

        if not host_name:
            host_name = self.environment_host

        if not settings.API_EXEC or host_name != settings.DEFAULT_HOST_NAME:
            host = self._host.retrieve(host_name)

        env.host = host.host if host else None
        env.port = host.port if host else None
        env.user = host.user if host else None
        env.token = host.token if host else None
        return env

    def create_env(self, name, **fields):
        env = self._environment.create(name)
        host = self._host.create('temp')

        env.host = host.host
        env.port = host.port
        env.user = host.user
        env.token = host.token

        for field, value in fields.items():
            setattr(env, field, value)
        return env

    def set_env(self, name = None, repo = None, image = None):
        self._environment.set_env(name, repo, image)
        self.success("Successfully updated current environment")

    def update_env_host(self, **fields):
        name = fields.pop('name', None)
        if not name:
            name = self.environment_host

        host = self._host.retrieve(name)
        if not host:
            host = self._host.create(name, **fields)
        else:
            for field, value in fields.items():
                setattr(host, field, value)
        host.save()

    def delete_env(self):
        self.exec_local('module clear')
        self._environment.delete_env()
        self.success("Successfully removed environment")


    def get_state(self, name, default = None):
        instance = self.get_instance(self._state, name, required = False)
        if instance:
            return instance.value
        return default

    def set_state(self, name, value = None):
        self._state.store(name, value = value)

    def delete_state(self, name = None, default = None):
        value = self.get_state(name, default)
        self._state.delete(name)
        return value

    def clear_state(self):
        self._state.clear()
