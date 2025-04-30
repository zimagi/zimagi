from utility.terminal import TerminalMixin

from .command import Command  # noqa: F401


class CommandIndex(TerminalMixin):

    def __init__(self):
        pass

    def find(self, args):
        print("hello world")
        print(args)
        return None
