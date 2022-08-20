from django.conf import settings

from utility.data import ensure_list, intersection, deep_merge, get_identifier

import oyaml


class Processor(object):

    def __init__(self, command, spec_key, plugin_key = None, display_only = False):
        self.command = command
        self.spec_key = spec_key
        self.plugin_key = plugin_key if plugin_key else self.spec_key
        self.processor_spec = settings.MANAGER.get_spec(self.spec_key)
        self.display_only = display_only


    def run(self, required_names = None, required_tags = None, ignore_requirements = False, field_values = None):
        if required_names is None:
            required_names = []
        if required_tags is None:
            required_tags = []
        if field_values is None:
            field_values = {}

        if self.processor_spec:
            process_map = self._order_processes(
                self.processor_spec,
                required_names = required_names,
                required_tags = required_tags,
                ignore_requirements = ignore_requirements
            )
            for priority, names in sorted(process_map.items()):
                self.command.run_list(
                    [ ( name, field_values ) for name in names ],
                    self.run_process
                )

    def run_process(self, process):
        name = process[0]
        params = process[1]
        spec = deep_merge(self.processor_spec.get(name, {}), params)
        if self.plugin_key not in spec:
            self.command.error("Attribute '{}' required for {} definition: {}".format(
                self.plugin_key,
                self.spec_key,
                name
            ))

        spec_display = oyaml.dump(spec, indent = 2)

        if self.display_only:
            self.command.data(name, "\n{}".format(spec_display), 'spec')
        else:
            param_display = "\n{}".format("\n".join([ "  {}".format(line) for line in oyaml.dump(params, indent = 2).split("\n") ])) if params else ''

            def run_provider():
                self.command.notice("Running {}: {}\n{}{}".format(self.spec_key, name, '-' * self.command.display_width, param_display))
                self.provider_process(name, spec)
                self.command.success("Completed {}: {}\n{}{}".format(self.spec_key, name, '-' * self.command.display_width, param_display))

            self.command.run_exclusive(
                "{}-{}-{}".format(self.plugin_key, name, get_identifier(spec)),
                run_provider,
                timeout = 0
            )

    def provider_process(self, name, spec):
        self.command.get_provider(
            self.plugin_key, spec[self.plugin_key], name, spec
        ).process()


    def _order_processes(self, spec, required_names, required_tags, ignore_requirements):
        priorities = {}
        priority_map = {}

        if required_names is None:
            required_names = []

        def _inner_dependencies(updated_names, top):
            dependencies = {}

            for name, config in spec.items():
                if config is not None and isinstance(config, dict):
                    tags = [ str(tag) for tag in ensure_list(config.get('tags', [])) ]
                    requires = ensure_list(config.get('requires', []))

                    if updated_names and name not in updated_names:
                        continue
                    if top and required_tags and len(intersection(tags, required_tags)) != len(required_tags):
                        continue

                    if ignore_requirements:
                        dependencies[name] = intersection(requires, updated_names)
                    else:
                        dependencies[name] = requires

            return dependencies

        top_level = True
        while True:
            dependencies = _inner_dependencies(required_names, top_level)

            for name, requires in dependencies.items():
                required_names.append(name)

                if not ignore_requirements:
                    for require in requires:
                        if require not in required_names:
                            required_names.append(require)

            required_names = list(set(required_names))
            if len(dependencies.keys()) == len(required_names):
                break

            top_level = False

        for name, requires in dependencies.items():
            priorities[name] = 0

        for index in range(0, len(dependencies.keys())):
            for name in list(dependencies.keys()):
                for require in dependencies[name]:
                    priorities[name] = max(priorities[name], priorities[require] + 1)

        for name, priority in priorities.items():
            if priority not in priority_map:
                priority_map[priority] = []
            priority_map[priority].append(name)

        return priority_map
