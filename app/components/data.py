from systems.commands import profile


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 25

    def run(self, name, config):
        provider = self.pop_value('_type', config)
        groups = self.pop_values('_groups', config)
        queries = self.pop_value('queries', config)
        required_types = []

        if not queries or not isinstance(queries, dict):
            self.command.error("Data {} requires 'queries' dictionary (with each element representing a data query to merge)".format(name))

        if not provider:
            provider = 'collection'

        for query_name, query_info in queries.items():
            for query_field, field_value in query_info.items():
                if query_field == 'required':
                    required_types.append(query_name)
                else:
                    config["{}:{}".format(query_name, query_field)] = field_value

        if required_types:
            config['required_types'] = required_types

        self.exec('data save',
            dataset_provider_name = provider,
            dataset_key = name,
            dataset_fields = config,
            groups_keys = groups
        )
