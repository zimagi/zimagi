from systems.commands.index import Command


class Clean(Command('db.clean')):

    def exec(self):
        self.clean_snapshots(self.keep_num)
