from django.conf import settings

from systems.command import providers
from utility.terraform import Terraform

import os


class TerraformWrapper(object):

    def __init__(self, provider):
        self.provider = provider
        self.terraform = Terraform(provider.command)
    
    def plan(self, type, instance):
        if type:
            manifest_path = self._get_manifest_path(type, instance.type)
            variables = self.provider.get_variables(instance)
            self.terraform.plan(manifest_path, variables, instance.state)
    
    def apply(self, type, instance):
        if type:
            manifest_path = self._get_manifest_path(type, instance.type)
            variables = self.provider.get_variables(instance)
            instance.state = self.terraform.apply(manifest_path, variables, instance.state)

    def destroy(self, type, instance):
        if type:
            manifest_path = self._get_manifest_path(type, instance.type)
            variables = self.provider.get_variables(instance)
            self.terraform.destroy(manifest_path, variables, instance.state)

    def _get_manifest_path(self, type, name):
        return os.path.join(settings.APP_DIR, 'terraform', type, "{}.tf".format(name))


class TerraformState(providers.DataProviderState):

    @property
    def variables(self):
        return self.get('outputs')


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
    
      
    def initialize_instance(self, instance, relations, created):
        self.initialize_terraform(instance, relations, created)

        if self.test:
            self.terraform.plan(self.terraform_type(), instance)
        else:
            self.terraform.apply(self.terraform_type(), instance)

    def initialize_terraform(self, instance, relations, created):
        # Override in subclass
        pass
    

    def finalize_instance(self, instance):
        self.finalize_terraform(instance)
        self.terraform.destroy(self.terraform_type(), instance)

    def finalize_terraform(self, instance):
        # Override in subclass
        pass
