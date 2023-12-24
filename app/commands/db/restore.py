from systems.commands.index import Command


class Restore(Command('db.restore')):

    def exec(self):
        self.restore_snapshot(self.snapshot_name)
