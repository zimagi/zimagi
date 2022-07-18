from django.conf import settings

from .mixins import annotations, filters, fields, relations, query, update, render
from utility.terminal import TerminalMixin


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


    def __init__(self, cls):
        self.model  = cls
        self.name   = self.meta.verbose_name.replace(' ', '_')
        self.plural = self.meta.verbose_name_plural.replace(' ', '_')

        super().__init__()


    @property
    def manager(self):
        return settings.MANAGER


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

    def get_packages(self):
        packages = [
            settings.DB_PACKAGE_ALL_NAME,
            self.name
        ]
        packages.extend(self.get_children(True))
        return list(set(packages))


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
