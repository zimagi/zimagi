from collections import OrderedDict


class RelationMixin(object):

    def parse_scope(self, facade):
        for name in facade.scope_parents:
            getattr(self, "parse_{}_key".format(name))("--{}".format(name.replace('_', '-')), tags = ['scope'])

    def set_scope(self, facade, optional = False):
        filters = {}
        for name in OrderedDict.fromkeys(facade.scope_parents).keys():
            instance_name = getattr(self, "{}_key".format(name), None)
            if optional and not instance_name:
                name = None

            if name and name in facade.fields:
                sub_facade = getattr(self, "_{}".format(
                    facade.get_subfacade(name).name
                ))
                if facade.name != sub_facade.name:
                    self.set_scope(sub_facade, optional)
                else:
                    sub_facade.set_scope(filters)

                if instance_name:
                    instance = self.get_instance(sub_facade, instance_name, required = not optional)
                    if instance:
                        filters["{}_id".format(name)] = instance.get_id()
                    elif not optional:
                        self.error("{} {} does not exist".format(facade.name.title(), instance_name))

        facade.set_scope(filters)
        return filters

    def get_scope_filters(self, instance):
        facade = instance.facade
        filters = {}
        for name, value in facade.get_scope_filters(instance).items():
            filters["{}_key".format(name)] = value
        return filters


    def parse_relations(self, facade):
        for field_name, info in facade.get_extra_relations().items():
            option_name = "--{}".format(field_name.replace('_', '-'))

            if info['multiple']:
                method_name = "parse_{}_keys".format(field_name)
            else:
                method_name = "parse_{}_key".format(field_name)

            getattr(self, method_name)(option_name, tags = ['relation'])

    def get_relations(self, facade):
        relations = {}
        for field_name, info in facade.get_extra_relations().items():
            base_name = info['model'].facade.name

            sub_facade = getattr(self, "_{}".format(base_name), None)
            if sub_facade:
                self.set_scope(sub_facade, True)

            if info['multiple']:
                accessor_name = "{}_keys".format(field_name)
            else:
                accessor_name = "{}_key".format(field_name)

            if getattr(self, "check_{}".format(accessor_name))():
                key_value = getattr(self, accessor_name)

                if info['multiple']:
                    value = []
                    for key in key_value:
                        instance = self.get_instance(sub_facade, key, required = False)
                        value.append(instance.get_id() if instance else key)
                else:
                    instance = self.get_instance(sub_facade, key_value, required = False)
                    value = instance.get_id() if instance else key_value

                relations[field_name] = value
        return relations
