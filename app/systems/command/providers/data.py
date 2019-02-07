from systems.models import AppModel
from .base import BaseCommandProvider

import datetime
import copy


class DataProviderState(object):

    def __init__(self, data):
        if isinstance(data, DataProviderState):
            self.state = data.export()
        else:
            self.state = data if isinstance(data, dict) else {}

    def export(self):
        return self.state


    def get_value(self, data, *keys):
        if isinstance(data, (dict, list, tuple)):
            name = keys[0]
            keys = keys[1:] if len(keys) > 1 else []
            
            if isinstance(data, dict):
                value = data.get(name, None)
            else:
                try:
                    value = data[name]
                except KeyError:
                    pass
            
            if not len(keys):
                return value
            else:
                return self.get_value(value, *keys)
            
        return None

    def get(self, *keys):
        return self.get_value(self.state, *keys)


    def get_resource(self, name):
        return self.get(name)

    def get_id(self, name):
        resource = self.get_resource(name)
        if resource:
            return self.get_value(resource, 'id')
        return None


class DataCommandProvider(BaseCommandProvider):

    @property
    def facade(self):
        # Override in subclass
        return None

    def provider_state(self):
        return DataProviderState

    def resource_variables(self):
        # Override in subclass
        return {}
 

    def get(self, name, required = True):
        instance = self.command.get_instance(self.facade, name, required = required)
        if getattr(instance, 'state', None):
            instance.state = self.provider_state()(instance.state)
    
    def get_variables(self, instance):
        variables = {}

        if getattr(instance, 'config', None) and isinstance(instance.config, dict):
            for name, value in instance.config.items():
                variables[name] = value
        
        if getattr(instance, 'variables', None) and isinstance(instance.variables, dict):
            for name, value in instance.variables.items():
                variables[name] = value
        
        for field in instance.facade.fields:
            value = getattr(instance, field)

            if field[0] != '_' and field not in ('config', 'variables', 'state'):
                variables[field] = value
            
            if value and isinstance(value, datetime.datetime):
                variables[field] = value.strftime("%Y-%m-%d %H:%M:%S %Z")

        for field, value in variables.items():
            if isinstance(value, AppModel):
                variables[field] = self.get_variables(value)
        
        return variables


    def initialize_instance(self, instance, created, test):
        # Override in subclass
        pass

    def finalize_instance(self, instance):
        # Override in subclass
        pass


    def store(self, reference, fields, test = False):
        model_fields = {}
        provider_fields = {}
        created = False
        
        self.config = copy.copy(fields)
        self.provider_config()
        self.validate()

        if isinstance(reference, AppModel):
            instance = reference
        else:
            instance = self.facade.retrieve(reference)
        
        if not instance:
            fields = self.config

        for field, value in fields.items():
            if field in self.facade.fields:
                model_fields[field] = fields[field]
            else:
                provider_fields[field] = fields[field]
        
        if not instance:
            instance = self.facade.create(reference, **model_fields)
            created = True
        else:
            for field, value in model_fields.items():
                setattr(instance, field, value)
                        
        instance.config = {**instance.config, **provider_fields}
        self.initialize_instance(instance, created, test)

        if test:
            self.command.success("Test complete")
        else:
            if getattr(instance, 'variables', None) is not None:
                instance.variables = self._collect_variables(instance)

            instance.save()
            self.command.success("Successfully saved {} {}".format(self.facade.name, instance.name))
        
        return instance


    def create(self, name, fields, test = False):
        if self.command.check_available(self.facade, name):
            return self.store(name, fields, test)
        return None

    def update(self, fields, test = False):
        if not self.instance:
            self.command.error("Updating an instance requires a valid instance given to provider on initialization")
        
        return self.store(self.instance, fields, test)

    def delete(self):
        if not self.instance:
            self.command.error("Deleting an instance requires a valid instance given to provider on initialization")
        
        self.finalize_instance(self.instance)

        if self.facade.delete(self.instance.name):
            self.command.success("Successfully deleted {} {}".format(self.facade.name, self.instance.name))
        else:
            self.command.error("{} {} deletion failed".format(self.facade.name.title(), self.instance.name))


    def _collect_variables(self, instance):
        variables = {}

        if getattr(instance, 'state', None) is not None:
            state = self.provider_state()(instance.state)
            for variable, resource in self.resource_variables().items():
                variables[variable] = state.get_id(resource)
        
        return variables


    def _get_field_info(self, fields):
        field_names = []
        field_labels = []

        for field in fields:
            if isinstance(field, (list, tuple)):
                field_names.append(field[0])
                field_labels.append(field[1])
            else:
                field_names.append(field)
                field_labels.append(field)
        
        return (field_names, field_labels)

    def _get_field_labels(self, processed_fields, existing_fields, labels):
        for index, value in enumerate(processed_fields):
            try:
                existing_index = existing_fields.index(value)
                processed_fields[index] = labels[existing_index]
            except Exception as e:
                pass
        
        return processed_fields
