from settings import Roles
from .storage import StorageActionCommand


class StorageMountActionCommand(StorageActionCommand):

    def get_priority(self):
        return 40

