from django.conf import settings

from systems.command import providers
from utility.terraform import Terraform

import os
import json


class TerraformWrapper(object):

    def __init__(self, provider):
        self.provider = provider
        self.terraform = Terraform(
            provider.command, 
            provider.command.force
        )
    
    def plan(self, type, instance, namespace = None):
        if type:
            manifest_path = self._get_manifest_path(type, instance.type)
            variables = self.provider.get_variables(instance, namespace)
            state = instance.state_config.get(namespace, {}) if namespace else instance.state_config
            self.terraform.plan(manifest_path, variables, state)
    
    def apply(self, type, instance, namespace = None):
        if type:
            manifest_path = self._get_manifest_path(type, instance.type)
            variables = self.provider.get_variables(instance, namespace)
            state = instance.state_config.get(namespace, {}) if namespace else instance.state_config
            state = self.terraform.apply(manifest_path, variables, state)
            if namespace:
                instance.state_config[namespace] = state
            else:
                instance.state_config = state

    def destroy(self, type, instance, namespace = None):
        if type:
            manifest_path = self._get_manifest_path(type, instance.type)
            variables = self.provider.get_variables(instance, namespace)
            state = instance.state_config.get(namespace, {}) if namespace else instance.state_config
            self.terraform.destroy(manifest_path, variables, state)

    def _get_manifest_path(self, type, name):
        return os.path.join(settings.APP_DIR, 'terraform', type, "{}.tf".format(name))


class TerraformState(providers.DataProviderState):

    @property
    def variables(self):
        variables = {}
        outputs = self.get('outputs')
        
        if outputs:
            for key, info in outputs.items():
                variables[key] = info['value']
        
        return variables


class TerraformProvider(providers.DataCommandProvider):

    def provider_state(self):
        return TerraformState

    def terraform_type(self):
        # Override in subclass
        return None
   

    @property
    def terraform(self):
        if not getattr(self, '_terraform_cache', None):
            self._terraform_cache = TerraformWrapper(self)
        return self._terraform_cache
    
      
    def initialize_instance(self, instance, created):
        self.initialize_terraform(instance, created)

        if self.test:
            self.terraform.plan(self.terraform_type(), instance)
        else:
            self.terraform.apply(self.terraform_type(), instance)

    def initialize_terraform(self, instance, created, object = None):
        # Override in subclass
        pass
    

    def finalize_instance(self, instance):
        self.finalize_terraform(instance)
        self.terraform.destroy(self.terraform_type(), instance)

    def finalize_terraform(self, instance, object = None):
        # Override in subclass
        pass
