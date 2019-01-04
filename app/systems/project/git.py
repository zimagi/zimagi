from .base import BaseProjectProvider


class Git(BaseProjectProvider):

    def provider_config(self):
        self.requirement('remote', help = 'Git remote to clone and pull updates')
        self.requirement('name', help = 'Unique name of project in environment')

        self.option('reference', 'master', help = 'Git branch, tag, or commit reference')


    def initialize_project(self, project):
        pass

    def destroy_project(self, project = None):
        if not self.project and not project:
            self.command.error("Destroying project requires a valid project instance given to provider on initialization")
        if not project:
            project = self.project
