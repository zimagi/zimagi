from github import Github, UnknownObjectException
from django.conf import settings

from systems.plugins.index import BaseProvider
from utility.ssh import SSH


class Provider(BaseProvider('module', 'github')):

    @property
    def github_token(self):
        token = settings.GITHUB_TOKEN
        if not token:
            self.command.error("To use GitHub module provider ZIMAGI_GITHUB_TOKEN environment variable must be specified")
        return token

    @property
    def github_org(self):
        org = settings.GITHUB_ORG
        if not org:
            self.command.error("To use GitHub module provider ZIMAGI_GITHUB_ORG environment variable or org/repo must be specified")
        return org


    @property
    def github(self):
        if not getattr(self, '_github', None):
            self._github = Github(self.github_token)
        return self._github


    def initialize_instance(self, instance, created):
        if not settings.GITHUB_TOKEN:
            super().initialize_instance(instance, created)
        else:
            create_deploy_key = False

            instance.config['username'] = 'git'

            if self.field_remote:
                instance.config['remote'] = self.field_remote if '/' in self.field_remote \
                    else "{}/{}".format(self.github_org, self.field_remote)

            instance.config['name'] = instance.config['remote'].split('/')[1] if not self.field_name \
                else self.field_name

            instance.name = instance.config['name']
            instance.remote = "{}@github.com:{}.git".format(instance.config['username'], instance.config['remote'])

            if not instance.secrets.get('private_key', None) or not instance.secrets.get('public_key', None):
                private_key, public_key = SSH.create_ecdsa_keypair()
                instance.secrets['private_key'] = private_key
                instance.secrets['public_key'] = public_key
                create_deploy_key = True

            repo, repo_created = self._get_repository(instance)

            if create_deploy_key:
                if 'deploy_key' in instance.variables:
                    repo.get_key(instance.variables['deploy_key']).delete()

                deploy_key = repo.create_key(
                    "@{}:{}".format(self.github.get_user().login, settings.APP_NAME),
                    public_key,
                    False
                )
                instance.variables['deploy_key'] = deploy_key.id

            if repo_created:
                self._provision_template(instance)
                self.init()
                self.commit("Initial template module files")
                self.push()
            else:
                super().initialize_instance(instance, created)


    def finalize_instance(self, instance):
        if settings.GITHUB_TOKEN:
            repo, repo_created = self._get_repository(instance, create = False)

            if repo and 'deploy_key' in instance.variables:
                repo.get_key(instance.variables['deploy_key']).delete()

        super().finalize_instance(instance)


    def _get_repository(self, instance, create = True):
        try:
            return (
                self.github.get_repo(instance.config['remote']),
                False
            )
        except UnknownObjectException:
            if create:
                org_name, repo_name = instance.config['remote'].split('/')
                org = self.github.get_organization(org_name)

                return (
                    org.create_repo(repo_name,
                        description = self.field_description,
                        private = not self.field_public,
                        auto_init = False,
                        allow_rebase_merge = True,
                        allow_squash_merge = True,
                        allow_merge_commit = True,
                        delete_branch_on_merge = False,
                        has_issues = True,
                        has_projects = False,
                        has_downloads = False,
                        has_wiki = False
                    ),
                    True
                )
            return (None, False)
