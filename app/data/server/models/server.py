
from systems import models
from data.environment import models as env
from data.server import models as server


class ServerFacade(models.ModelFacade):

    def key(self):
        return 'name'
 
    def scope(self, fields = False):
        if fields:
            return ('environment',)
        
        state = env.Environment.facade.get_curr()
        if not state:
            return False

        return { 'environment_id': state.value }


    def render(self, *fields, **filters):
        data = super().render(*fields, **filters)
        
        pw_index = data[0].index('password')
        pub_key_index = data[0].index('public_key')
        priv_key_index = data[0].index('private_key')

        for index in range(1, len(data)):
            record = data[index]
            
            if record[pw_index]:
                record[pw_index] = '*****'
            
            if record[pub_key_index]:
                record[pub_key_index] = '*****'

            if record[priv_key_index]:
                record[priv_key_index] = '*****'

        return data


class Server(models.AppModel):
    name = models.CharField(max_length=128)
    ssh_ip = models.CharField(max_length=128)
    ip = models.CharField(max_length=128)
    
    user = models.CharField(max_length=128, null=False)
    password = models.CharField(max_length=256, null=False)
    public_key = models.TextField()
    private_key = models.TextField()

    environment = models.ForeignKey(env.Environment, related_name='servers', on_delete=models.CASCADE)
    groups = models.ManyToManyField(server.Group, related_name='servers', blank=True)

    class Meta:
        unique_together = ('environment', 'name')
        facade_class = ServerFacade

    def __str__(self):
        return "{} ({})".format(self.name, self.ip)
