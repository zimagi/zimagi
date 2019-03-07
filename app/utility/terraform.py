from django.conf import settings

from utility.temp import temp_dir

import os
import pathlib
import json


class TerraformError(Exception):
    pass


class Terraform(object):

    def __init__(self, command, ignore = False):
        self.command = command
        self.ignore = ignore


    def init(self, temp, display = False):
        terraform_command = (
            'terraform',
            'init',
            '-force-copy'
        )
        success, stdout, stderr = self.command.sh(
            terraform_command,
            cwd = temp.temp_path,
            display = display
        )
        if not success and not self.ignore:
            raise TerraformError("Terraform init failed: {}".format(" ".join(terraform_command)))


    def plan(self, manifest_path, variables, state, display_init = False):
        with temp_dir() as temp:
            temp.link(manifest_path, 'manifest.tf')

            self.save_variable_index(temp, variables)
            if state:
                self.save_state(temp, state)

            self.init(temp, display_init)

            terraform_command = (
                'terraform',
                'plan',
                "-var-file={}".format(self.save_variables(temp, variables))
            )
            success, stdout, stderr = self.command.sh(
                terraform_command,
                cwd = temp.temp_path,
                display = True
            )
            if not success and not self.ignore:
                raise TerraformError("Terraform plan failed: {}".format(" ".join(terraform_command)))


    def apply(self, manifest_path, variables, state, display_init = False):
        with temp_dir() as temp:
            temp.link(manifest_path, 'manifest.tf')

            self.save_variable_index(temp, variables)
            if state:
                self.save_state(temp, state)

            self.init(temp, display_init)

            terraform_command = (
                'terraform',
                'apply',
                '-auto-approve',
                "-var-file={}".format(self.save_variables(temp, variables))
            )
            success, stdout, stderr = self.command.sh(
                terraform_command,
                cwd = temp.temp_path,
                display = True
            )
            if not success and not self.ignore:
                raise TerraformError("Terraform apply failed: {}".format(" ".join(terraform_command)))

            self.command.info('')
            return self.load_state(temp)


    def destroy(self, manifest_path, variables, state, display_init = False):
        with temp_dir() as temp:
            temp.link(manifest_path, 'manifest.tf')

            self.save_variable_index(temp, variables)
            if state:
                self.save_state(temp, state)

            self.init(temp, display_init)

            terraform_command = [
                'terraform',
                'destroy',
                '-auto-approve',
                "-var-file={}".format(self.save_variables(temp, variables))
            ]
            success, stdout, stderr = self.command.sh(
                terraform_command,
                cwd = temp.temp_path,
                display = True
            )
            if not success and not self.ignore:
                raise TerraformError("Terraform destroy failed: {}".format(" ".join(terraform_command)))


    def save_variable_index(self, temp, variables):
        index = []

        for name, value in variables.items():
            if isinstance(value, dict):
                data_type = self.parse_object(value, '  ')
            elif isinstance(value, (list, tuple)):
                data_type = 'list(string)'
            else:
                data_type = 'string'

            index.extend([
                'variable "{}" {{'.format(name),
                '  type = {}'.format(data_type),
                '}'
            ])
        return temp.save("\n".join(index), 'variables.tf')

    def parse_object(self, variables, prefix):
        object = ['object({']
        inner_prefix = prefix + '  '

        for key, value in variables.items():
            if isinstance(value, dict):
                object.append("{}{} = {}".format(inner_prefix, key, self.parse_object(value, inner_prefix)))
            elif isinstance(value, (list, tuple)):
                object.append("{}{} = list(string)".format(inner_prefix, key))
            else:
                object.append("{}{} = string".format(inner_prefix, key))

        object.append("{}}})".format(prefix))
        return "\n".join(object)


    def save_variables(self, temp, variables):
        return temp.save(json.dumps(variables), extension = 'tfvars.json')


    def save_state(self, temp, state):
        return temp.save(json.dumps(state), 'terraform.tfstate')

    def load_state(self, temp):
        return json.loads(temp.load('terraform.tfstate'))