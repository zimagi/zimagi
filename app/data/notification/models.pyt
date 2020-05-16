from django.db import models as django

from data.group.models import Group
from data.environment import models as environment
from data.mixins import resource
from systems.models import fields


class NotificationFacade(
    environment.EnvironmentBaseFacadeMixin
):
    def get_field_group_names_display(self, instance, value, short):
        display = []
        for record in instance.groups.all():
            display.append(record.group.name)

        return self.dynamic_color("\n".join(display) + "\n")

    def get_field_failure_group_names_display(self, instance, value, short):
        display = []
        for record in instance.failure_groups.all():
            display.append(record.group.name)

        return self.dynamic_color("\n".join(display) + "\n")


class NotificationGroupFacade(
    resource.ResourceBaseFacadeMixin
):
    def key(self):
        return 'id'


class Notification(
    environment.EnvironmentBase
):
    class Meta:
        verbose_name = "notification"
        verbose_name_plural = "notifications"
        facade_class = NotificationFacade
        dynamic_fields = ['group_names', 'failure_group_names']


class NotificationGroup(resource.ResourceBase):
    name = None
    notification = django.ForeignKey(Notification, related_name='groups', on_delete=django.CASCADE)
    group = django.ForeignKey(Group, null = False, on_delete = django.CASCADE, related_name = '+')

    class Meta:
        verbose_name = "notification group"
        verbose_name_plural = "notification groups"
        facade_class = NotificationGroupFacade
        ordering = ('id',)

    def __str__(self):
        return "{} ({})".format(self.notification.name, self.group.name)

    def get_id_fields(self):
        return ('notification_id', 'group_id')


class NotificationFailureGroup(resource.ResourceBase):
    name = None
    notification = django.ForeignKey(Notification, related_name='failure_groups', on_delete=django.CASCADE)
    group = django.ForeignKey(Group, null = False, on_delete = django.CASCADE, related_name = '+')

    class Meta:
        verbose_name = "notification failure group"
        verbose_name_plural = "notification failure groups"
        facade_class = NotificationGroupFacade
        ordering = ('id',)

    def __str__(self):
        return "{} ({})".format(self.notification.name, self.group.name)

    def get_id_fields(self):
        return ('notification_id', 'group_id')
