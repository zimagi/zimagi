from systems.commands.index import Command


class Backup(Command("db.backup")):
    def exec(self):
        self.create_snapshot()
