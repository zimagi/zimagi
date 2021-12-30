from .base import BaseMigration, MigrationError


class Migration(BaseMigration):

    def initialize(self):
        pass


    def migrate(self):
        # Find all models with encrypted fields
        # Query and backup all records for found models (old_cipher)
        # Update all encrypted fields for records of found models (new_cipher)
        # Destroy backup on success
        for name, info in self._find_models().items():
            pass

    def recover(self):
        pass


    def _find_models(self):
        # Find all models with encrypted fields
        models = {}

        return models