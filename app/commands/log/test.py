from systems.commands.index import Command


class Test(Command('log.test')):

    def exec(self):
        for number in range(100):
            self.data("Number", number)
            self.sleep(2)
