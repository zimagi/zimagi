from systems.commands.index import Command


class Snapshots(Command("db.snapshots")):
    def exec(self):
        self.system_info(" Zimagi Snapshots")
        self.spacing()

        for snapshot_file in self.get_snapshots():
            self.info(f" * {self.key_color(snapshot_file)}")

        self.spacing()
