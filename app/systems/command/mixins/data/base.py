
from systems.command import args
from utility import text


class DataMixin(object):
    
    def _parse_variable(self, name, type, help_text, optional = False):
        self.add_schema_field(name, 
            args.parse_var(self.parser, name, type, help_text, optional), 
            optional
        )

    def _parse_variables(self, name, value_label, flag, type, help_text, optional = False):
        if optional and flag:
            help_text = "{} (comma separated)".format(help_text)
            self.add_schema_field(name,
                args.parse_csv_option(self.parser, name, flag, help_text, None),
                True
            )
        else:
            self.add_schema_field(name,
                args.parse_vars(self.parser, name, value_label, type, help_text, optional),
                False
            )

    def _parse_fields(self, facade, name, optional = False, excluded_fields = [], help_callback = None):
        if help_callback and callable(help_callback):
            help_text = "\n".join(help_callback())
        else:
            required = [x for x in facade.required if x not in list(excluded_fields)]
            optional = [x for x in facade.optional if x not in excluded_fields]
            help_text = "\n".join(text.wrap("fields as key value pairs\n\nrequirements: {}\n\noptions: {}".format(", ".join(required), ", ".join(optional)), 60))

        self.add_schema_field(name,
            args.parse_key_values(self.parser, name, 'field=value', help_text, optional),
            optional
        )


    def _load_instance(self, facade, name, instance = None):
        if not instance:
            instance = facade.retrieve(name)

            if not instance:
                self.error("{} {} does not exist".format(facade.name, name))
        
        return instance

    def _load_instances(self, facade, names, instances = None):
        if not instances:
            for name in names:
                instance = facade.retrieve(name)

                if not instance:
                    self.error("{} {} does not exist".format(facade.name, name))

                instances.append(instance)
        
        return instances
