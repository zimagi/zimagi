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

    def __init__(self, data):
        super().__init__(data)
        self.resources = {}

        for resource in data['resources']:
            name = "{}.{}".format(resource['type'], resource['name'])
            self.resources[name] = resource

    def get_resource(self, name):
        return self.get_value(self.resources, name)

    def get_id(self, name):
        return self.get_value(self.get_resource(name), 'instances', 0, 'attributes', 'id')


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
    
      
    def initialize_instance(self, instance, created, test):
        self.initialize_provider(instance, created)

        if test:
            self.terraform.plan(self.terraform_type(), instance)
        else:
            self.terraform.apply(self.terraform_type(), instance)

    def initialize_provider(self, instance, created):
        # Override in subclass
        pass
    

    def finalize_instance(self, instance):
        self.finalize_provider(instance)
        self.terraform.destroy(self.terraform_type(), instance)

    def finalize_provider(self, instance):
        # Override in subclass
        pass
