from django.db import models as django

from data.group.models import Group
from systems.models import fields, resource, environment


class NotificationFacade(
    environment.EnvironmentModelFacadeMixin
):
    pass

class NotificationGroupFacade(
    resource.ResourceModelFacadeMixin
):
    def key(self):
        return 'id'


class Notification(
    environment.EnvironmentModel
):
    class Meta:
        verbose_name = "notification"
        verbose_name_plural = "notifications"
        facade_class = NotificationFacade
        dynamic_fields = ['groups', 'failure_groups']


class NotificationGroup(resource.ResourceModel):
    name = None
    notification = django.ForeignKey(Notification, related_name='groups', on_delete=django.CASCADE)
    group = django.ForeignKey(Group, null = False, on_delete = django.PROTECT, related_name = '+')

    class Meta:
        verbose_name = "notification group"
        verbose_name_plural = "notification groups"
        facade_class = NotificationGroupFacade
        ordering = ('id',)

    def __str__(self):
        return "{} ({})".format(self.notification.name, self.group.name)

    def get_id_fields(self):
        return ('notification_id', 'group_id')


class NotificationFailureGroup(resource.ResourceModel):
    name = None
    notification = django.ForeignKey(Notification, related_name='failure_groups', on_delete=django.CASCADE)
    group = django.ForeignKey(Group, null = False, on_delete = django.PROTECT, related_name = '+')

    class Meta:
        verbose_name = "notification failure group"
        verbose_name_plural = "notification failure groups"
        facade_class = NotificationGroupFacade
        ordering = ('id',)

    def __str__(self):
        return "{} ({})".format(self.notification.name, self.group.name)

    def get_id_fields(self):
        return ('notification_id', 'group_id')
