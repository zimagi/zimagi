from django.db import models


class State(models.Model):

    name = models.CharField(primary_key=True, max_length=256)      
    value = models.TextField()
    timestamp = models.DateTimeField(null=True)
    
    def  __str__(self):
        return "Config: {} ({})".format(self.name, self.value)


class Environment(models.Model):

    name = models.CharField(primary_key=True, max_length=256)      
    
    def  __str__(self):
        return "Env: {}".format(self.name)
   