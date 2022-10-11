from django.db.models.base import ModelBase
from django.db.models.fields.related import lazy_related_operation, RelatedField

import copy
import logging


logger = logging.getLogger(__name__)


_base_model_new = ModelBase.__new__

def _override_model_new(cls, name, bases, attrs, **kwargs):
    orig_attrs = copy.copy(attrs)
    try:
        return _base_model_new(cls, name, bases, attrs, **kwargs)
    except RuntimeError as e:
        for key, value in orig_attrs.items():
            attrs[key] = value

        if 'Meta' in attrs:
            attrs['Meta'].abstract = True
        else:
            attrs['Meta'] = type('Meta', (object,), {
                'abstract': True
            })
        logger.info("Converting model {} to an abstract object because it is not in INSTALLED_APPS".format(name))
        return _base_model_new(cls, name, bases, attrs, **kwargs)

ModelBase.__new__ = _override_model_new


def _contribute_to_class_override(self, cls, name, private_only = False, **kwargs):
    super(RelatedField, self).contribute_to_class(cls, name, private_only = private_only, **kwargs)

    self.opts = cls._meta

    if not cls._meta.abstract:
        class_name = cls.__name__.lower()
        class_attributes = list(cls.__dict__.keys())
        app_label = cls._meta.app_label.lower()
        data_name = getattr(cls._meta, 'data_name', class_name)

        if self.remote_field.related_name:
            related_name = self.remote_field.related_name
        else:
            related_name = self.opts.default_related_name
        if related_name:
            related_name = related_name % {
                "class": class_name,
                "model_name": cls._meta.model_name.lower(),
                "data_name": data_name,
                "app_label": app_label,
            }
            if related_name in class_attributes:
                related_name = "{}_set".format(related_name)

            self.remote_field.related_name = related_name

        if self.remote_field.related_query_name:
            related_query_name = self.remote_field.related_query_name % {
                "class": class_name,
                "data_name": data_name,
                "app_label": app_label,
            }
            if related_query_name in class_attributes:
                related_query_name = "{}_set".format(related_query_name)

            self.remote_field.related_query_name = related_query_name

        def resolve_related_class(model, related, field):
            field.remote_field.model = related
            field.do_related_class(related, model)

        lazy_related_operation(
            resolve_related_class, cls, self.remote_field.model, field = self
        )

RelatedField.contribute_to_class = _contribute_to_class_override
