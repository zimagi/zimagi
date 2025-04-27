import logging
import re

from django.db.models import Model
from utility.data import ensure_list, normalize_dict
from utility.query import get_queryset

from ..errors import RestrictedError, UpdateError

logger = logging.getLogger(__name__)


class ModelFacadeUpdateMixin:
    def create(self, key, values=None):
        if values is None:
            values = {}

        values[self.key()] = key
        self._check_scope(values)
        return self.model(**values)

    def get_or_create(self, key):
        instance = self.retrieve(key)
        if not instance:
            instance = self.create(key)
        return instance

    def split_field_values(self, values):
        scope_index = self.get_scope_relations()
        relation_index = self.get_extra_relations()
        reverse_index = self.get_reverse_relations()
        scope = {}
        fields = {}
        relations = {}
        reverse = {}

        for field, value in values.items():
            index_field = re.sub(r"_id$", "", field)

            if index_field in scope_index:
                if isinstance(value, Model):
                    scope[index_field] = value
                else:
                    scope[f"{index_field}_id"] = value

            elif index_field in relation_index:
                relation_field_info = relation_index[index_field]

                if not relation_field_info["multiple"]:
                    if isinstance(value, Model):
                        scope[index_field] = value
                    else:
                        scope[f"{index_field}_id"] = value
                else:
                    relations[field] = value

            elif index_field in reverse_index:
                reverse[field] = value
            else:
                fields[field] = value

        return scope, fields, relations, reverse

    def process_fields(self, fields, instance):
        object_fields = [*self.list_fields, *self.dictionary_fields, *self.encrypted_fields]
        processed = {}

        def set_nested_value(data, keys, value):
            key = keys.pop(0)
            if keys:
                if key not in data or not data[key]:
                    data[key] = {}
                set_nested_value(data[key], keys, value)
            else:
                data[key] = value

        for field, value in fields.items():
            add_field = True
            if "__" in field:
                field_components = field.split("__")
                base_field = field_components.pop(0)
                if base_field in object_fields:
                    if base_field not in processed:
                        processed[base_field] = getattr(instance, base_field, {})

                    set_nested_value(processed[base_field], field_components, value)
                    add_field = False

            if add_field:
                processed[field] = value

        return processed

    def store(self, key, values=None, command=None, relation_key=False, normalize=True):
        if values is None:
            values = {}

        if normalize:
            values = normalize_dict(values)

        scope, fields, relations, reverse = self.split_field_values(values)
        filters = {self.key(): key} if key else {}

        self.set_scope(scope)
        instance = self.retrieve(key, **filters) if key else None
        created = False

        if not instance:
            instance = self.create(key, filters)
            created = True

        for field, value in self.process_fields(fields, instance).items():
            setattr(instance, field, value)

        instance.save()
        self.save_relations(instance, relations, relation_key=relation_key, command=command)
        return (instance, created)

    def save_relations(self, instance, relations, relation_key=False, command=None):
        relation_index = self.get_extra_relations()
        resave = False

        for field, value in relations.items():
            index_field = re.sub(r"_id$", "", field)

            if command and relation_key:
                facade = command.facade(relation_index[index_field]["model"].facade.name)
            else:
                facade = relation_index[index_field]["model"].facade

            if relation_index[index_field]["multiple"]:
                self._update_related(facade, instance, field, value, relation_key, command)
            else:
                self._set_related(facade, instance, field, value, relation_key, command)
                resave = True

        if resave:
            instance.save()

    def _update_related(self, facade, instance, relation, ids, use_key, command):
        queryset = get_queryset(instance, relation)

        if ids is None:
            if queryset:
                queryset.clear()
            else:
                raise UpdateError(
                    f"Instance {getattr(instance, instance.facade.key())} relation {relation} is not a valid queryset"
                )
        else:
            all_ids = []
            input_ids = []
            add_ids = []
            remove_ids = []

            if queryset:
                id_field = facade.key() if use_key else facade.pk
                for sub_instance in queryset.all():
                    all_ids.append(getattr(sub_instance, id_field))

            for id in ids:
                if isinstance(id, (str, float, int)):
                    id = str(id)

                    if id.startswith("+"):
                        add_ids.append(id[1:])
                    elif id.startswith("-"):
                        remove_ids.append(id[1:])
                    else:
                        input_ids.append(id)
                else:
                    try:
                        input_ids.append(getattr(id, facade.pk))
                    except Exception:
                        pass

            if input_ids:
                if use_key:
                    input_values = [id.split(":")[-1] for id in input_ids]
                    remove_ids = []

                    for id in all_ids:
                        if id not in input_values:
                            remove_ids.append(id)
                else:
                    remove_ids = list(set(all_ids) - set(input_ids))

                add_ids = input_ids

            if add_ids:
                self._add_related(facade, instance, relation, add_ids, use_key, command)
            if remove_ids:
                self._remove_related(facade, instance, relation, remove_ids, use_key, command)

    def _add_related(self, facade, instance, relation, ids, use_key, command):
        queryset = get_queryset(instance, relation)
        instance_name = type(instance).__name__.lower()
        auto_create = facade.check_auto_create()

        if queryset:
            for id in ids:
                if ":" in id:
                    # provider:id
                    id_components = id.split(":")
                    provider_type = id_components[0]
                    id = id_components[1]
                else:
                    provider_type = "base"

                if use_key:
                    sub_instance = facade.retrieve(id)
                else:
                    sub_instance = facade.retrieve_by_id(id)

                if command and auto_create and not sub_instance:
                    if getattr(facade, "provider_name", None):
                        provider = command.get_provider(facade.provider_name, provider_type)
                        sub_instance = provider.create(id)
                    else:
                        sub_instance, created = facade.store(id)

                if sub_instance:
                    try:
                        queryset.add(sub_instance)
                    except Exception as e:
                        raise UpdateError(f"{facade.name.title()} add failed: {str(e)}")
                elif command and auto_create:
                    raise UpdateError(
                        f"{facade.name.title()} '{id}' creation failed for attachment to {instance.facade.name} '{str(instance)}'"  # noqa: E501
                    )
                else:
                    raise UpdateError(
                        f"{facade.name.title()} '{id}' does not exist for attachment to {instance.facade.name} '{str(instance)}'"  # noqa: E501
                    )
        else:
            raise UpdateError(f"There is no relation {relation} on {instance_name} class")

    def _remove_related(self, facade, instance, relation, ids, use_key, command):
        queryset = get_queryset(instance, relation)
        instance_name = type(instance).__name__.lower()

        if use_key:
            key = getattr(instance, instance.facade.key())
            keep_index = instance.facade.keep_relations().get(relation, {})
            keep = ensure_list(keep_index.get(key, []))

        if queryset:
            for id in ids:
                if not use_key or id not in keep:
                    if use_key:
                        # [provider:]id
                        id_components = id.split(":")
                        id = id_components[1] if len(id_components) > 1 else id_components[0]
                        sub_instance = facade.retrieve(id)
                    else:
                        sub_instance = facade.retrieve_by_id(id)

                    if sub_instance:
                        try:
                            queryset.remove(sub_instance)
                        except Exception as e:
                            raise UpdateError(f"{facade.name.title()} remove failed: {str(e)}")
                elif use_key:
                    raise UpdateError(f"{facade.name.title()} '{id}' removal from {key} is restricted")
        else:
            raise UpdateError(f"There is no relation {relation} on {instance_name} class")

    def _set_related(self, facade, instance, relation, id, use_key, command):
        if id is None:
            setattr(instance, relation, None)
        else:
            if isinstance(id, str):
                auto_create = facade.check_auto_create()

                if re.match(r"(none|null)", id, re.IGNORECASE):
                    setattr(instance, relation, None)
                else:
                    if use_key:
                        # [provider:]id
                        id_components = id.split(":")
                        provider_type = id_components[0] if len(id_components) > 1 else "base"
                        id = id_components[1] if len(id_components) > 1 else id_components[0]

                        sub_instance = facade.retrieve(id)

                        if command and auto_create and not sub_instance:
                            if getattr(facade, "provider_name", None):
                                provider = command.get_provider(facade.provider_name, provider_type)
                                sub_instance = provider.create(id)
                            else:
                                sub_instance, created = facade.store(id)
                    else:
                        sub_instance = facade.retrieve_by_id(id)

                    if sub_instance:
                        setattr(instance, relation, sub_instance)
                    elif command and auto_create:
                        raise UpdateError(
                            f"{facade.name.title()} '{id}' creation failed for attachment to {instance.facade.name} '{str(instance)}'"  # noqa: E501
                        )
                    else:
                        raise UpdateError(
                            f"{facade.name.title()} '{id}' does not exist for attachment to {instance.facade.name} '{str(instance)}'"  # noqa: E501
                        )
            else:
                setattr(instance, relation, id)

    def delete(self, key, **filters):
        if key not in ensure_list(self.keep(key)):
            filters[self.key()] = key
            return self.clear(**filters)
        else:
            raise RestrictedError(f"Removal of {self.model.__name__.lower()} {key} is restricted")

    def clear(self, **filters):
        queryset = self.filter(**filters)
        keep_list = self.keep()
        if keep_list:
            queryset = queryset.exclude(**{f"{self.key()}__in": ensure_list(keep_list)})

        deleted, del_per_type = queryset.delete()
        if deleted:
            return True
        return False
