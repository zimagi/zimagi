from systems.commands.index import Agent

import random


class Agent3(Agent('test.agent3')):

    def exec(self):
        self.success("Running agent 3")
        self.sleep(random.randint(0, 15))
