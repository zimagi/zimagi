from io import StringIO

from django.conf import settings
from django.core.management.base import CommandError

from systems.command import providers
from utility import ssh as sshlib

import threading
import time
import copy


class SSHAccessError(CommandError):
    pass


class BaseComputeProvider(providers.TerraformProvider):

    def __init__(self, name, command, instance = None):
        super().__init__(name, command, instance)
        self.provider_type = 'server'
        self.provider_options = settings.SERVER_PROVIDERS

    def terraform_type(self):
        return 'compute'

    @property
    def facade(self):
        return self.command._server

    def prepare_instance(self, instance, created):
        if not self.check_ssh(instance = instance):
            self.command.error("Can not establish SSH connection to: {}".format(instance), error_cls = SSHAccessError)


    def rotate_key(self):
        instance = self.check_instance('server rotate key')
        (private_key, public_key) = sshlib.SSH.create_keypair()

        ssh = self.ssh()
        ssh.exec('mkdir -p "$HOME/.ssh"')
        ssh.exec('chmod 700 "$HOME/.ssh"')
        ssh.exec('echo "{}" > "$HOME/.ssh/authorized_keys"'.format(public_key))
        ssh.exec('chmod 600 "$HOME/.ssh/authorized_keys"')
        
        instance.private_key = private_key

    def rotate_password(self):
        instance = self.check_instance('server rotate password')
        password = sshlib.SSH.create_password()

        self.command.project.provider.exec(
            'password',
            instance,
            {
                "user": instance.user, 
                "password": password
            }
        )
        instance.password = password


    def ssh(self, timeout = 10, port = 22):
        instance = self.check_instance('server ssh')
        return self.command.ssh(instance, timeout = timeout, port = port)

    def check_ssh(self, port = 22, tries = 10, interval = 2, timeout = 10, silent = False, instance = None):
        if not self.instance and not instance:
            self.command.error("Checking SSH requires a valid server instance given to provider on initialization")
        if not instance:
            instance = self.instance

        host = "{}:{}".format(instance.ip, port)

        while True:
            if not tries:
                break
            try:
                if not silent:
                    self.command.info("Checking {}@{} SSH connection".format(instance.user, host))
                
                sshlib.SSH(host, instance.user, instance.password, 
                    key = instance.private_key, 
                    timeout = timeout
                )
                return True
            
            except Exception as e:
                time.sleep(interval)
                tries -= 1
        
        return False

    def ping(self, port = 22):
        self.check_instance('server ping')
        return self.check_ssh(
            port = port,
            tries = 1,
            timeout = 1,
            silent = True
        )
