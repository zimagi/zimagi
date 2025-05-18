from systems.commands.index import CommandMixin


class PlatformMixin(CommandMixin("platform")):
    def get_host(self, name=None):
        if not name:
            name = self.platform_host
        return self.get_instance(self._host, name, required=False, cache=False)

    def create_host(self, **fields):
        name = fields.pop("name", "temp")
        host = self._host.create(name)
        for field, value in fields.items():
            setattr(host, field, value)
        return host

    def save_host(self, **fields):
        name = fields.pop("name", self.platform_host)
        host = self.get_host(name)
        if not host:
            host = self.create_host(**{"name": name, **fields})
        else:
            for field, value in fields.items():
                setattr(host, field, value)
        host.save()
        return host

    def get_state(self, name, default=None):
        instance = self.get_instance(self._state, name, required=False, cache=False)
        if instance:
            return instance.value
        return default

    def set_state(self, name, value=None):
        self._state.store(name, {"value": value}, command=self)

    def delete_state(self, name=None, default=None):
        value = self.get_state(name, default)
        self._state.delete(name)
        return value

    def clear_state(self):
        self._state.clear()
