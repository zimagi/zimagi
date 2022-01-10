from .base import BaseTest


class Test(BaseTest):

    def exec(self):
        print(self.api.list('group').results)
