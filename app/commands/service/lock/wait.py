from systems.commands.index import Command
from utility.mutex import Mutex


class Wait(Command("service.lock.wait")):
    def exec(self):
        success = Mutex.wait(*self.keys, timeout=self.timeout, interval=self.interval)
        if self.raise_error and not success:
            self.error(f"Lock timeout waiting for keys: {", ".join(self.keys)}")
