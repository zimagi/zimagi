from systems.commands.index import Command


class Snapshots(Command('db.snapshots')):

    def exec(self):
        self.info(' Zimagi Snapshots')
        self.info('')

        for snapshot_file in self.get_snapshots():
            self.info(" * {}".format(
                self.key_color(snapshot_file)
            ))
        self.info('')
