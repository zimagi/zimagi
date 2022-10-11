from functools import lru_cache

from django.db.models.fields.related import ForeignKey, OneToOneField, ManyToManyField
from django.db.models.fields.reverse_related import ManyToOneRel, OneToOneRel, ManyToManyRel

import re


class ModelFacadeRelationMixin(object):

    @lru_cache(maxsize = None)
    def get_children(self, recursive = False):
        children = []

        for model in self.manager.index.get_models():
            model_fields = { f.name: f for f in model._meta.fields }
            scope_fields = model.facade.scope_fields

            for scope_field in scope_fields:
                field = model_fields[re.sub(r'_id$', '', scope_field)]

                if isinstance(field, ForeignKey):
                    if self.model == field.related_model:
                        children.append({
                            'facade': model.facade,
                            'field': field
                        })
                        if recursive:
                            children.extend(model.facade.get_children(True))
        return children


    @lru_cache(maxsize = None)
    def get_parent_relations(self):
        parent_relations = {}
        for field in self.meta.get_fields():
            if isinstance(field, OneToOneField) and field.name.endswith('_ptr'):
                parent_relations[field.related_model.facade.name] = {
                    'name': field.name,
                    'label': field.name.replace('_', ' ').title(),
                    'model': field.related_model,
                    'field': field,
                    'multiple': False
                }
        return parent_relations

    @lru_cache(maxsize = None)
    def get_scope_relations(self):
        scope_relations = {}
        for field in self.meta.get_fields():
            if field.name in self.scope_fields:
                scope_relations[field.name] = {
                    'name': field.name,
                    'label': field.name.replace('_', ' ').title(),
                    'model': field.related_model,
                    'field': field,
                    'multiple': False
                }
        return scope_relations

    @lru_cache(maxsize = None)
    def get_extra_relations(self):
        scope_fields = self.scope_fields
        relations = {}
        for field in self.meta.get_fields():
            if field.name not in scope_fields and isinstance(field, (ForeignKey, ManyToManyField, OneToOneField)):
                if not field.name.endswith('_ptr'):
                    if isinstance(field, ManyToManyField):
                        multiple = True
                    elif isinstance(field, (ForeignKey, OneToOneField)):
                        multiple = False

                    relations[field.name] = {
                        'name': field.name,
                        'label': "{}{}".format(field.name.replace('_', ' ').title(), ' (M)' if multiple else ''),
                        'model': field.related_model,
                        'field': field,
                        'multiple': multiple
                    }
        return relations

    @lru_cache(maxsize = None)
    def get_referenced_relations(self):
        return {
            **self.get_scope_relations(),
            **self.get_extra_relations()
        }

    @lru_cache(maxsize = None)
    def get_reverse_relations(self):
        relations = {}
        for field in self.meta.get_fields():
            if field.auto_created and not field.concrete:
                if isinstance(field, (OneToOneRel, ManyToOneRel)):
                    multiple = False
                elif isinstance(field, ManyToManyRel):
                    multiple = True

                field_info = {
                    'name': field.name,
                    'label': "{}{}".format(field.name.replace('_', ' ').title(), ' (M)' if multiple else ''),
                    'model': field.related_model,
                    'field': field,
                    'multiple': multiple
                }
                if self.get_reverse_field(field_info):
                    relations[field.name] = field_info
        return relations

    @lru_cache(maxsize = None)
    def get_all_relations(self):
        return {
            **self.get_referenced_relations(),
            **self.get_reverse_relations()
        }


    def get_subfacade(self, field_name):
        field = self.field_index[field_name]
        return field.related_model.facade


    def get_reverse_field(self, field_info):
        field_map = {}

        for related_field_name, related_info in field_info['model'].facade.get_referenced_relations().items():
            if related_info['model'].facade.name == self.name:
                field_map[related_info['field'].remote_field.related_name] = related_field_name

        return field_map.get(field_info['name'], None)
