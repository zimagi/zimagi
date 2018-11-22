from django.db import models
from django.utils.timezone import now

from data.environment import models as env


class Group(models.Model):
    name = models.CharField(primary_key=True, max_length=256)
    parent = models.ForeignKey("Group", null=True, on_delete=models.CASCADE)


class Server(models.Model):
    name = models.CharField(max_length=128)
    ssh_ip = models.CharField(max_length=128)
    ip = models.CharField(max_length=128)
    
    user = models.CharField(max_length=128, null=False)
    password = models.CharField(max_length=256, null=False)
    public_key = models.TextField()
    private_key = models.TextField()

    environment = models.ForeignKey(env.Environment, related_name='servers', on_delete=models.CASCADE)
    groups = models.ManyToManyField(Group, related_name='servers', blank=True)

    created = models.DateTimeField(null=False)
    updated = models.DateTimeField(null=True)

    class Meta:
        unique_together = ('environment', 'name')


    def __str__(self):
        return "{} ({})".format(self.name, self.ip)
