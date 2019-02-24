from systems.models.base import AppModel
from systems.project.provisioner import core, network
from utility.data import ensure_list, clean_dict

import copy


class ProjectProfile(
    core.ConfigMixin,
    core.ProjectMixin,
    network.NetworkMixin,
    network.FirewallMixin,
    network.SubnetMixin
):
    def __init__(self, project, data):
        self.project = project
        self.command = project.command
        self.data = data
        self.components = []
        
        self.ensure_configs()
        self.ensure_projects()
        self.load_parents()
        

    def provision(self, components = [], params = {}):
        self.data = self.get_schema()
        self.components = components

        self.set_config(params)
        self.ensure_networks()
        self.ensure_firewalls()
        self.ensure_subnets()


    def export(self, components = []):
        self.data = self.get_schema()
        self.components = components

        self.export_configs()
        self.export_projects()
        self.export_networks()
        self.export_firewalls()
        self.export_subnets()

        return copy.deepcopy(self.data)

    def _export(self, name, instances, describe_callback = None, use_config = True, namespace = None):
        index = {}
        for instance in instances:
            if describe_callback and callable(describe_callback):
                variables = describe_callback(instance)
            else:
                variables = {}
            
            index[instance.name] = self.get_variables(instance, variables,
                use_config = use_config,
                namespace = namespace
            )        
        self.data[name] = index


    def destroy(self, components = []):
        self.data = self.get_schema()
        self.components = components
        
        self.destroy_subnets()
        self.destroy_firewalls()
        self.destroy_networks()


    def load_parents(self):
        self.parents = []
        if 'parents' in self.data:
            for parent in ensure_list(self.data['parents']):
                project = self.get_project(parent['project'])
                self.parents.append(project.provider.get_profile(parent['profile']))

    def get_parents(self):
        parents = []
        for profile in self.parents:
            parents.extend(profile.get_parents())
            parents.append(profile)
        return parents


    def get_schema(self):
        schema = {}
        for profile in self.parents:
            self.merge_schema(schema, profile.get_schema())
        self.merge_schema(schema, self.data)
        return schema

    def merge_schema(self, schema, data):
        for key, value in data.items():
            if isinstance(value, dict):
                schema.setdefault(key, {})
                self.merge_schema(schema[key], value)
            else:
                schema[key] = value


    def include(self, component):
        if not self.components or component in self.components:
            return True
        return False

        
    def get_variables(self, instance, variables = {}, use_config = True, namespace = None):
        if use_config and getattr(instance, 'config', None) and isinstance(instance.config, dict):
            config = instance.config.get(namespace, {}) if namespace else instance.config
            for name, value in config.items():
                variables[name] = value
        
        for field in instance.facade.fields:
            value = getattr(instance, field)

            if not isinstance(value, AppModel) and field[0] != '_' and field not in (
                'name',
                'config', 
                'variables', 
                'state', 
                'created', 
                'updated'
            ):
                variables[field] = value
       
        return clean_dict(variables)
