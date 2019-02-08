from django.conf import settings

from utility.temp import temp_dir

import os
import pathlib
import json


class Terraform(object):
    
    def __init__(self, command):
        self.command = command


    def init(self, temp):
        terraform_command = (
            'terraform', 
            'init', 
            '-force-copy'
        )
        success, stdout, stderr = self.command.sh(
            terraform_command,
            cwd = temp.temp_path,
            display = True
        )
        if not success:
            self.command.error("Terraform init failed: {}".format(" ".join(terraform_command)))


    def plan(self, manifest_path, variables, state):
        with temp_dir() as temp:
            temp.link(manifest_path, 'manifest.tf')

            self.save_variable_index(temp, variables)
            if state:
                self.save_state(temp, state)
            
            self.init(temp)

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
            if not success:
                self.command.error("Terraform plan failed: {}".format(" ".join(terraform_command)))


    def apply(self, manifest_path, variables, state):
        with temp_dir() as temp:
            temp.link(manifest_path, 'manifest.tf')

            self.save_variable_index(temp, variables)
            if state:
                self.save_state(temp, state)
            
            self.init(temp)

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
            if not success:
                self.command.error("Terraform apply failed: {}".format(" ".join(terraform_command)))
            
            return self.load_state(temp)


    def destroy(self, manifest_path, variables, state):
        with temp_dir() as temp:
            temp.link(manifest_path, 'manifest.tf')

            self.save_variable_index(temp, variables)
            if state:
                self.save_state(temp, state)
            
            self.init(temp)

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
            if not success:
                self.command.error("Terraform destroy failed: {}".format(" ".join(terraform_command)))


    def save_variable_index(self, temp, variables):
        index = []

        for name, value in variables.items():
            if isinstance(value, dict):
                data_type = self.parse_object(value, '  ')
            elif isinstance(value, (list, tuple)):
                data_type = 'list'
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
                object.append("{}{} = list".format(inner_prefix, key))
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