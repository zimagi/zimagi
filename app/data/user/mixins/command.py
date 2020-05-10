from data.user.models import User
from .base import DataMixin


class UserMixin(DataMixin):

    schema = {
        'user': {
            'model': User,
            'provider': True
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['00_user'] = self._user
