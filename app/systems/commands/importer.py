from django.conf import settings

from utility.data import ensure_list, intersection

import oyaml


class Importer(object):

    def __init__(self, command, display_only = False):
        self.command = command
        self.import_spec = settings.MANAGER.get_spec('import')
        self.display_only = display_only


    def run(self, required_names = None, required_tags = None, ignore_requirements = False):
        if required_names is None:
            required_names = []
        if required_tags is None:
            required_tags = []

        if self.import_spec:
            import_map = self._order_imports(
                self.import_spec,
                required_names = required_names,
                required_tags = required_tags,
                ignore_requirements = ignore_requirements
            )
            for priority, names in sorted(import_map.items()):
                self.command.run_list(names, self.run_import)

    def run_import(self, name):
        spec = self.import_spec.get(name, {})
        if 'source' not in spec:
            self.command.error("Attribute 'source' required for import definition: {}".format(name))

        if self.display_only:
            self.command.data(name, "\n{}".format(oyaml.dump(spec, indent = 2)))
        else:
            def import_source():
                self.command.notice("Running import: {}".format(name))
                self.command.get_provider(
                    'source', spec['source'], name, spec
                ).update()
                self.command.success("Completed import: {}".format(name))

            self.command.run_exclusive("importer-{}".format(name), import_source, wait = False)


    def _order_imports(self, spec, required_names, required_tags, ignore_requirements):
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
