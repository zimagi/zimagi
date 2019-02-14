
from systems import models
from data.environment import models as env
from data.config import models as config
from utility.data import number, serialize, unserialize


class ConfigFacade(models.ModelFacade):

    def __init__(self, cls):
        super().__init__(cls)
        self.fields.append('value')

    def get_packages(self):
        return super().get_packages() + ['environment', 'config']


    def key(self):
        return 'name'
 
    def scope(self, fields = False):
        if fields:
            return ('environment',)
        
        curr_env = env.Environment.facade.get_env()
        if not curr_env:
            return False

        return { 'environment_id': curr_env }
    

    def render(self, fields, queryset_values):
        fields = list(fields)
        data = [fields]

        for item in queryset_values:
            record = []

            for field in fields:
                if field in ['created', 'updated'] and item[field]:
                    value = item[field].strftime("%Y-%m-%d %H:%M:%S %Z")
                elif field == '_value' and item[field][0] in ('{', '['):
                    value = json.dumps(unserialize(item[field]), indent=2)
                else:
                    value = item[field]

                record.append(value)
            data.append(record)

        return data


class Config(models.AppModel):
    name = models.CharField(max_length=256)      
    _value = models.TextField(db_column="value", null=True)
    user = models.CharField(null=True, max_length=40)
    
    environment = models.ForeignKey(env.Environment, related_name='config', on_delete=models.PROTECT)
    groups = models.ManyToManyField(config.ConfigGroup, related_name='config')

    @property
    def value(self):
        if getattr(self, '_cached_value', None) is None:
            self._cached_value = unserialize(self._value)
        return self._cached_value

    @value.setter
    def value(self, data):
        self._value = serialize(data)        
        self._cached_value = None

    class Meta:
        unique_together = ('environment', 'name')
        facade_class = ConfigFacade

    def  __str__(self):
        return "{} ({})".format(self.name, self.value)

    def initialize(self, command):
        groups = list(self.groups.values_list('name', flat = True))
        
        if groups and not command.check_access(groups):
            return False
        
        return True

    def add_groups(self, groups):
        groups = [groups] if isinstance(groups, str) else groups
        for group in groups:
            group, created = config.ConfigGroup.objects.get_or_create(name = group)
            self.groups.add(group)

    def remove_groups(self, groups):
        groups = [groups] if isinstance(groups, str) else groups
        self.groups.filter(name__in = groups).delete()
