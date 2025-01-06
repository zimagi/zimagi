from systems.commands.index import Command
from utility.mutex import Mutex


class Wait(Command("service.lock.wait")):
    def exec(self):
        Mutex.wait(*self.keys, timeout=self.timeout, interval=self.interval)
