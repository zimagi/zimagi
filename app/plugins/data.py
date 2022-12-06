from plugins import base
from systems.models.base import BaseModel
from utility.data import normalize_dict, deep_merge

import copy


class BasePlugin(base.BasePlugin):

    @classmethod
    def generate(cls, plugin, generator):
        super().generate(plugin, generator)

        def facade(self):
            if getattr(self, '_facade', None):
                return self._facade
            return self.command.facade(generator.spec['data'])

        def store_lock_id(self):
            return generator.spec['store_lock']

        def delete_lock_id(self):
            return generator.spec['delete_lock']

        if generator.spec.get('data', None):
            plugin.facade = property(facade)

        if generator.spec.get('store_lock', None):
            plugin.store_lock_id = store_lock_id

        if generator.spec.get('delete_lock', None):
            plugin.delete_lock_id = delete_lock_id


    def __init__(self, type, name, command, instance = None):
        super().__init__(type, name, command)
        self.instance = instance


    def check_instance(self, op):
        if not self.instance:
            self.command.error("Provider {} operation '{}' requires a valid model instance given to provider on initialization".format(self.name, op))
        return self.instance

    def get(self, name, required = True):
        return self.command.get_instance(self.facade, name, required = required)


    @property
    def facade(self):
        # Override in subclass
        return None


    def initialize_instances(self):
        # Override in subclass
        pass

    def preprocess_fields(self, fields, instance = None):
        # Override in subclass
        return fields

    def initialize_instance(self, instance, created):
        # Override in subclass
        pass

    def prepare_instance(self, instance, created):
        # Override in subclass
        pass

    def store_related(self, instance, created, test):
        # Override in subclass
        pass

    def finalize_instance(self, instance):
        # Override in subclass
        pass


    def _init_config(self, fields, create = True):
        self.create_op = create
        self.config = copy.copy(fields)
        self.provider_config()
        self.validate()


    def store_lock_id(self):
        # Override in subclass
        return None

    def store(self, key, values, relation_key = True, quiet = False):
        instance = None
        model_fields = {}
        provider_fields = {}
        provider_secrets = {}
        created = False

        # Initialize instance
        scope, fields, relations, reverse = self.facade.split_field_values(values)
        secret_fields = self.get_secret_fields()

        self.facade.set_scope(scope)

        if key is not None:
            if isinstance(key, BaseModel):
                instance = key
            else:
                instance = self.facade.retrieve(key)

        if not instance:
            fields = { **self.config, **self.secrets, **fields }
            instance = self.facade.create(key)
            created = True

        fields['provider_type'] = self.name

        for field, value in self.facade.process_fields(fields, instance).items():
            if field in self.facade.fields:
                if value is not None:
                    model_fields[field] = value
            elif field in secret_fields:
                provider_secrets[field] = value
            else:
                provider_fields[field] = value

        for field, value in model_fields.items():
            setattr(instance, field, value)

        instance.config = deep_merge(instance.config, provider_fields)
        instance.secrets = deep_merge(instance.secrets, provider_secrets)

        self.instance = instance

        def process():
            # Save instance
            self.initialize_instance(instance, created)

            if self.test:
                self.store_related(instance, created, True)
                self.command.success("Test complete")
            else:
                try:
                    self.prepare_instance(instance, created)
                    instance.save()

                except Exception as e:
                    if created:
                        if not quiet:
                            self.command.info("Save failed, now reverting any associated resources...")
                        self.finalize_instance(instance)
                    raise e

                self.facade.save_relations(
                    instance,
                    relations,
                    relation_key = relation_key,
                    command = self.command
                )
                self.store_related(instance, created, False)
                if not quiet:
                    self.command.success("Successfully saved {} '{}'".format(self.facade.name, getattr(instance, instance.facade.key())))

        self.run_exclusive(self.store_lock_id(), process)
        return instance


    def create(self, key, values = None, relation_key = True, quiet = False, normalize = True):
        if not values:
            values = {}
        if normalize:
            values = normalize_dict(values)

        if self.command.check_available(self.facade, key):
            values = self.preprocess_fields(values)

            self._init_config(values, True)
            return self.store(key, values, relation_key = relation_key, quiet = quiet)
        else:
            self.command.error("Instance '{}' already exists".format(key))

    def update(self, values = None, relation_key = True, quiet = False, normalize = True):
        if not values:
            values = {}
        if normalize:
            values = normalize_dict(values)

        instance = self.check_instance('instance update')
        values = self.preprocess_fields(values, instance)

        self._init_config(values, False)
        return self.store(instance, values, relation_key = relation_key, quiet = quiet)


    def delete_lock_id(self):
        # Override in subclass
        return None

    def delete(self, force = False):
        instance = self.check_instance('instance delete')
        instance_id = getattr(instance, instance.facade.pk)
        instance_key = getattr(instance, instance.facade.key())

        def process():
            if self.facade.keep(instance_key):
                self.command.error("Removal of {} {} is restricted (has dependencies)".format(self.facade.name, instance_key))

            for child in self.facade.get_children():
                sub_facade = child['facade']
                field = child['field']

                for sub_instance in sub_facade.filter(**{ "{}_id".format(field.name): instance_id }):
                    if getattr(sub_facade, 'provider_name', None):
                        sub_instance.initialize(self.command)
                        sub_instance.provider.delete(force)
                    else:
                        sub_facade.clear(**{ sub_facade.pk: getattr(sub_instance, sub_facade.pk) })
            try:
                self.finalize_instance(instance)
            except Exception as e:
                if not force:
                    raise e

            if self.facade.delete(instance_key):
                self.command.success("Successfully deleted {} '{}'".format(self.facade.name, instance_key))
            else:
                self.command.error("{} '{}' deletion failed".format(self.facade.name.title(), instance_key))

        self.run_exclusive(self.delete_lock_id(), process)
