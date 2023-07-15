from systems.commands.index import Command


class Gpus(Command('gpus')):

    def exec(self):
        self.sh('nvidia-smi')
