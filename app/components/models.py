from systems.commands import profile


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 7

    def run(self, name, config):
        fields = self.pop_info('fields', config)

        if fields:
            if not isinstance(fields, dict):
                self.command.error("Model {} fields value must be a dictionary of fields".format(name))
            else:
                errors = []
                for field, info in fields.items():
                    if not isinstance(info, dict) or 'type' not in info:
                        errors.append("Field {} on model {} must be a dictionary with a 'type' key specified".format(field, name))
                if errors:
                    self.command.error("\n".join(errors))

        self.exec(name, 'template generate',
            module_key = self.profile.module.instance.name,
            module_template = 'data/model',
            template_fields = {
                **config,
                'name': name
            }
        )

        def save_field(field_name):
            field_info = fields[field_name]

            self.exec(name, 'template generate',
                module_key = self.profile.module.instance.name,
                module_template = "field/{}".format(field_info['type']),
                template_fields = {
                    **field_info.get('options', {}),
                    'data_name': name,
                    'field_name': field_name
                }
            )

        if fields:
            self.run_list(fields.keys(), save_field)
