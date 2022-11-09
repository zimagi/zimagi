from django.conf import settings

from .errors import ProviderError
from .mixins import annotations, filters, fields, relations, query, update, render
from utility.terminal import TerminalMixin
from utility.data import flatten

import threading


class ModelFacade(
    TerminalMixin,
    filters.ModelFacadeFilterMixin,
    fields.ModelFacadeFieldMixin,
    relations.ModelFacadeRelationMixin,
    annotations.ModelFacadeAnnotationMixin,
    query.ModelFacadeQueryMixin,
    update.ModelFacadeUpdateMixin,
    render.ModelFacadeRenderMixin
):
    _viewset = {}

    thread_lock = threading.Lock()


    def __init__(self, cls):
        self.model  = cls
        self.name   = self.meta.verbose_name.replace(' ', '_')
        self.plural = self.meta.verbose_name_plural.replace(' ', '_')

        super().__init__()


    @property
    def manager(self):
        return settings.MANAGER


    def get_provider(self, type, name, *args, **options):
        base_provider = self.manager.index.get_plugin_base(type)
        providers = self.manager.index.get_plugin_providers(type, True)

        if name is None or name in ('help', 'base'):
            provider_class = base_provider
        elif name in providers.keys():
            provider_class = providers[name]
        else:
            raise ProviderError("Plugin {} provider {} not supported".format(type, name))

        try:
            return provider_class(type, name, None, *args, **options)
        except Exception as e:
            raise ProviderError("Plugin {} provider {} error: {}".format(type, name, e))


    def get_viewset(self):
        from systems.api.data.views import DataViewSet
        if self.name not in self._viewset:
            self._viewset[self.name] = DataViewSet(self)
        return self._viewset[self.name]

    def check_api_enabled(self):
        return False


    @property
    def meta(self):
        return self.model._meta

    def get_packages(self, exclude = None):
        if exclude is None:
            exclude = []

        packages = [
            settings.DB_PACKAGE_ALL_NAME,
            self.name if self.name not in exclude else []
        ]
        for field_name, relation in self.get_referenced_relations().items():
            if relation['model'].facade.name not in exclude:
                packages.extend(relation['model'].facade.get_packages(exclude + [ self.name ]))

        return list(set(flatten(packages)))


    def _ensure(self, command, reinit = False):
        # Added dynamically in the model index
        pass

    def ensure(self, command, reinit):
        # Override in subclass
        pass

    def keep(self, key = None):
        # Override in subclass
        return []

    def keep_relations(self):
        # Override in subclass
        return {}
