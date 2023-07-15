from systems.commands.index import Agent

import random


class Agent2(Agent('test.agent2')):

    def exec(self):
        self.success("Running agent 2")
        self.sleep(random.randint(0, 15))
