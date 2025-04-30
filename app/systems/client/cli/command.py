from utility.terminal import TerminalMixin


class Command(TerminalMixin):

    def __init__(self):
        pass

    def exec(self, argv):
        print(argv)
        pass
