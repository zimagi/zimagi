from systems.commands.index import Command
from utility.mutex import Mutex


class Clear(Command('service.lock.clear')):

    def exec(self):
        Mutex.clear(*self.keys)
