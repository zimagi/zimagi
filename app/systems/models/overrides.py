from django.db.models.base import ModelBase

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
