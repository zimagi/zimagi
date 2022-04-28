from systems.commands import profile


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 25

    def run(self, name, config):
        provider = self.pop_value('_type', config)
        groups = self.pop_values('_groups', config)
        frames = self.pop_value('frames', config)
        required_types = []

        if not frames or not isinstance(frames, dict):
            self.command.error("Data {} requires 'frames' dictionary (with each frame representing a data query to merge)".format(name))

        if not provider:
            provider = 'collection'

        for frame_name, frame_info in frames.items():
            for frame_field, field_value in frame_info.items():
                if frame_field == 'required':
                    required_types.append(frame_name)
                else:
                    config["{}:{}".format(frame_name, frame_field)] = field_value

        if required_types:
            config['required_types'] = required_types

        self.exec('data save',
            dataset_provider_name = provider,
            dataset_name = name,
            dataset_fields = config,
            groups_names = groups
        )
