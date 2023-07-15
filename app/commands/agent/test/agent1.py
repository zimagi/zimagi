from systems.commands.index import Agent

import random


class Agent1(Agent('test.agent1')):

    def exec(self):
        self.success("Running agent 1")
        self.sleep(random.randint(0, 15))
