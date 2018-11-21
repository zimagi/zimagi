from django.db import models
from django.utils.timezone import now


class State(models.Model):

    name = models.CharField(primary_key=True, max_length=256)      
    value = models.TextField()
    timestamp = models.DateTimeField(null=True)


    def  __str__(self):
        return "{} ({})".format(self.name, self.value)


    @classmethod
    def get_environment(cls):
        try:
            state = cls.objects.get(name = 'environment')
        except cls.DoesNotExist:
            return None

        return state

    @classmethod
    def set_environment(cls, environment):
        state, created = cls.objects.get_or_create(
            name = 'environment'
        )
        state.value = environment
        state.timestamp = now()
        state.save()

        return (state, created)

    @classmethod
    def delete_environment(cls):
        state = cls.get_environment()

        if state:
            deleted, del_per_type = state.delete()
            
            if deleted:
                return True
        
        return False


class Environment(models.Model):

    name = models.CharField(primary_key=True, max_length=256)      

    def  __str__(self):
        return "{}".format(self.name)


    @classmethod
    def get_keys(cls):
        return list(cls.objects.all().values_list('name', flat = True))

    @classmethod
    def retrieve(cls, environment):
        try:
            data = cls.objects.get(name = environment)
        except cls.DoesNotExist:
            return None

        return data

    @classmethod
    def store(cls, environment):
        return cls.objects.get_or_create(name = environment)

    @classmethod
    def delete(cls, environment):
        deleted, del_per_type = cls.objects.filter(name = environment).delete()

        if deleted:
            return True
        return False

    @classmethod
    def clear(cls):
        deleted, del_per_type = cls.objects.all().delete()

        if deleted:
            return True
        return False 