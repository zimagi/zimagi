from systems.commands.index import Command


class Children(Command("group.children")):
    def exec(self):
        self.exec_local(
            "group save", {"group_key": self.group_key, "group_provider_name": self.group_provider_name, "verbosity": 0}
        )
        parent = self._group.retrieve(self.group_key)
        for group in self.group_child_keys:
            self._group.store(group, {"provider_type": parent.provider_type, "parent": parent}, command=self)
        self.success(f"Successfully saved group {parent.name}")
