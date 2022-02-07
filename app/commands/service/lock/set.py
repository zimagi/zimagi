from systems.commands.index import Command
from utility.mutex import Mutex


class Set(Command('service.lock.set')):

    def exec(self):
        Mutex.set(self.key)
