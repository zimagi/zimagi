from systems.command import types, mixins


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
