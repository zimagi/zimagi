from django.conf import settings

from utility.project import ProjectDir


class MigrationError(Exception):
    pass


class BaseMigration(object):

    def __init__(self, name, old_cipher, new_cipher):
        self.name = name
        self.old_cipher = old_cipher
        self.new_cipher = new_cipher

        self.disk = ProjectDir(
            "encryption", self.name, base_path=settings.ROOT_LIB_DIR, env=True
        )
        self.initialize()

    def initialize(self):
        # Override in sub classes if needed
        pass

    def finalize(self):
        # Implement in sub classes if needed
        pass

    def run(self):
        try:
            self.migrate()
            self.disk.delete()

        except MigrationError as error:
            error_message = [str(error)]
            try:
                self.recover()
                self.disk.delete()

            except MigrationError as error:
                error_message.append(str(error))

            raise MigrationError("\n\n".join(error_message))
        finally:
            self.finalize()

    def migrate(self):
        raise NotImplementedError(
            "All encryption migration classes must implement the migrate method"
        )

    def recover(self):
        raise NotImplementedError(
            "All encryption migration classes must implement the recover method"
        )
