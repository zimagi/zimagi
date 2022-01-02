from django.utils.timezone import now

from systems.models.index import ModelMixin


class ResourceMixin(ModelMixin('resource')):

    def _set_created_time(self):
        if self.created is None:
            self.created = now()

    def _prepare_save(self):
        self._set_created_time()

        filters = {}
        self.facade._check_scope(filters)
        for field, value in filters.items():
            if value is not None:
                setattr(self, field, value)
