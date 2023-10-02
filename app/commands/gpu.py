from systems.commands.index import Command


class Gpu(Command('gpu')):

    def exec(self):
        self.sh('nvidia-smi')
