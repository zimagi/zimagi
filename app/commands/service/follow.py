from systems.commands.index import Command


class Follow(Command("service.follow")):
    def exec(self):
        for package in self.listen(self.channel, state_key=self.state_key, timeout=self.timeout, block_sec=1):
            self.separator()
            self.data("Time", package.time, "time")
            self.data("Sender", package.sender, "sender")
            self.data("Message", package.message, "message")
