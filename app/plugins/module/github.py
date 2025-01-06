import pygit2
from django.conf import settings
from github import Github, UnknownObjectException
from systems.plugins.index import BaseProvider
from utility.ssh import SSH


class Provider(BaseProvider("module", "github")):
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
            self.command.error(
                "To use GitHub module provider ZIMAGI_GITHUB_ORG environment variable or org/repo must be specified"
            )
        return org

    @property
    def github(self):
        if not getattr(self, "_github", None):
            self._github = Github(self.github_token)
        return self._github

    def get_remote(self, instance):
        return "{}@github.com:{}.git".format(instance.config["username"], instance.config["remote"])

    def initialize_instance(self, instance, created, retry=True):
        if not settings.GITHUB_TOKEN:
            self.command.error("To use GitHub module provider ZIMAGI_GITHUB_TOKEN environment variable must be specified")
        else:
            instance.config["username"] = "git"

        if self.field_remote:
            instance.config["remote"] = (
                self.field_remote if "/" in self.field_remote else f"{self.github_org}/{self.field_remote}"
            )

            instance.remote = self.field_remote

        create_deploy_key = False
        if not instance.secrets.get("private_key", None) or not instance.secrets.get("public_key", None):
            private_key, public_key = SSH.create_ecdsa_keypair()
            instance.secrets["private_key"] = private_key
            instance.secrets["public_key"] = public_key
            create_deploy_key = True

        repo, repo_created = self._get_repository(instance)

        if repo_created:
            instance.name = instance.remote.split("/")[-1] if not self.field_name else self.field_name

        if create_deploy_key:
            deploy_key_title = f"@{self.github.get_user().login}:{settings.APP_NAME}"

            for deploy_key in repo.get_keys():
                if deploy_key.title == deploy_key_title:
                    deploy_key.delete()

            deploy_key = repo.create_key(deploy_key_title, public_key, False)
            instance.variables["deploy_key"] = deploy_key.id

            self.command.sleep(5)

        if not settings.DISABLE_MODULE_SYNC and repo_created:
            self._provision_template(instance)
            self.init()
            self.commit("Initial template module files")
            self.push()
        else:
            try:
                super().initialize_instance(instance, created)
            except pygit2.GitError as e:
                if retry and str(e).startswith("Failed to retrieve list of SSH authentication methods"):
                    if instance.variables.get("deploy_key", None):
                        try:
                            deploy_key = repo.get_key(instance.variables["deploy_key"])
                            deploy_key.delete()
                        except UnknownObjectException:
                            pass

                        instance.variables.pop("deploy_key")

                    instance.secrets.pop("private_key", None)
                    instance.secrets.pop("public_key", None)

                    self.initialize_instance(instance, created, False)
                else:
                    raise e

    def finalize_instance(self, instance):
        if settings.DISABLE_MODULE_SYNC:
            return

        if not settings.GITHUB_TOKEN:
            self.command.error("To use GitHub module provider ZIMAGI_GITHUB_TOKEN environment variable must be specified")

        repo, repo_created = self._get_repository(instance, create=False)

        if repo and "deploy_key" in instance.variables:
            repo.get_key(instance.variables["deploy_key"]).delete()

        super().finalize_instance(instance)

    def _get_repository(self, instance, create=True):
        try:
            return (self.github.get_repo(instance.config["remote"]), False)
        except UnknownObjectException:
            if create:
                org_name, repo_name = instance.config["remote"].split("/")
                org = self.github.get_organization(org_name)

                return (
                    org.create_repo(
                        repo_name,
                        description=self.field_description,
                        private=not self.field_public,
                        auto_init=False,
                        allow_rebase_merge=True,
                        allow_squash_merge=True,
                        allow_merge_commit=True,
                        delete_branch_on_merge=False,
                        has_issues=True,
                        has_projects=False,
                        has_downloads=False,
                        has_wiki=False,
                    ),
                    True,
                )
            return (None, False)
