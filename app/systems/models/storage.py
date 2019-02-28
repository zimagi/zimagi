from django.db import models as django

from data.storage.models import Storage
from .resource import ResourceModel, ResourceModelFacadeMixin


class StorageModelFacadeMixin(ResourceModelFacadeMixin):

    def set_scope(self, storage):
        super().set_scope(storage_id = storage.id)

    def get_field_storage_display(self, instance, value, short):
        return str(value)
 
    def get_field_storage_sources_display(self, instance, value, short):
        storage = [ str(x) for x in value.all() ]
        return "\n".join(storage)


class StorageMixin(django.Model):

    storage = django.ForeignKey(Storage, on_delete=django.PROTECT, related_name='+')

    class Meta:
        abstract = True

class StorageRelationMixin(django.Model):
 
    storage = django.ManyToManyField(Storage, related_name='+')
 
    class Meta:
        abstract = True


class StorageModel(StorageMixin, ResourceModel):

    class Meta(ResourceModel.Meta):
        abstract = True
        unique_together = ('storage', 'name')

    def __str__(self):
        return "{}:{}".format(self.storage.name, self.name)

    def get_id_fields(self):
        return ('name', 'storage_id')
