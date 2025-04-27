from django.conf import settings

from systems.plugins.index import BaseProvider
from utility.data import get_identifier

import os


class Provider(BaseProvider('encoder', 'transformer')):

    @classmethod
    def initialize(cls, instance, init):
        if not getattr(cls, '_transformer', None):
            cls._transformer = {}

        if init and instance.identifier not in cls._transformer:
            os.environ['HF_HOME'] = settings.MANAGER.hf_cache

            cls._transformer[instance.identifier] = cls._get_transformer(instance)


    @classmethod
    def _get_model_name(cls):
        raise NotImplementedError("Method _get_model_name() must be implemented in sub classes")

    @classmethod
    def _get_transformer(cls, instance):
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(cls._get_model_name(),
            cache_folder = settings.MANAGER.st_model_cache,
            device = instance.field_device,
            token = settings.HUGGINGFACE_TOKEN
        )

    def _get_identifier(self, init):
        return get_identifier([ super()._get_identifier(init), self._get_model_name() ])


    @property
    def transformer(self):
        return self._transformer[self.identifier]


    def encode(self, sentences, **config):
        if not sentences:
            return []
        return self.transformer.encode(sentences).tolist()
