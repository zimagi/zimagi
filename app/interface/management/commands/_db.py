from systems.command import types


class LoadCommand(
    types.DatabaseActionCommand
):
    def parse(self):
        self.parse_db_dir()
        self.parse_no_encrypt()
        self.parse_project_name()
        self.parse_file_name()

    def exec(self):
        self.db.load_file(
            self.db_file_path(self.project), 
            not self.no_encrypt
        )
        self.success("Successfully loaded database")


class RestoreCommand(
    types.DatabaseActionCommand
):
    def preprocess(self, params):
        params.data['db'] = self.db.save('all', encrypted = True)

    def exec(self):
        self.db.load(self.options.get('db'), encrypted = True)
        self.success('Database successfully transferred')


class SaveCommand(
    types.DatabaseActionCommand
):
    def parse(self):
        self.parse_db_dir()
        self.parse_no_encrypt()
        self.parse_project_name()
        self.parse_file_name()

    def exec(self):
        self.db.save_file(
            self.db_file_path(self.project), 
            not self.no_encrypt
        )
        self.success("Successfully saved database")


class Command(types.DatabaseRouterCommand):

    def get_command_name(self):
        return 'db'

    def get_subcommands(self):
        return (
            ('load', LoadCommand),
            ('restore', RestoreCommand),
            ('save', SaveCommand)
        )
