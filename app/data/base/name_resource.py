from systems.models.index import BaseModel


class NameResourceBase(BaseModel('name_resource')):

    def save(self, *args, **kwargs):
        self._prepare_save()
        super().save(*args, **kwargs)
