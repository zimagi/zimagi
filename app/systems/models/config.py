from systems import models


class ConfigModelFacadeMixin(models.ModelFacade):
    pass


class ConfigMixin(object):

    config = models.EncryptedTextField(default={})
