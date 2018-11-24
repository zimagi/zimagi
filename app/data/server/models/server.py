
from systems import models
from data.environment import models as env


class ServerFacade(models.ModelFacade):

    def key(self):
        return 'name'
 
    def scope(self):
        state = env.State.facade.get_env()

        if not state:
            return False
        
        return { 'environment': state.value }


class Server(models.AppModel):
    name = models.CharField(max_length=128)
    ssh_ip = models.CharField(max_length=128)
    ip = models.CharField(max_length=128)
    
    user = models.CharField(max_length=128, null=False)
    password = models.CharField(max_length=256, null=False)
    public_key = models.TextField()
    private_key = models.TextField()

    environment = models.ForeignKey(env.Environment, related_name='servers', on_delete=models.CASCADE)
    groups = models.ManyToManyField(Group, related_name='servers', blank=True)

    class Meta:
        unique_together = ('environment', 'name')
        facade_class = ServerFacade

    def __str__(self):
        return "{} ({})".format(self.name, self.ip)
