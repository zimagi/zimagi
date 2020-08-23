from django.conf import settings

from utility.data import ensure_list, intersection


class Importer(object):

    def __init__(self, command):
        self.command = command
        self.import_spec = settings.MANAGER.index.spec.get('import', {})


    def run(self, required_names = [], ignore_requirements = False):
        if self.import_spec:
            import_map = self._order_imports(
                self.import_spec,
                required_names = required_names,
                ignore_requirements = ignore_requirements
            )
            for priority, names in sorted(import_map.items()):
                self.command.run_list(names, self.run_import)

    def run_import(self, name):
        spec = self.import_spec.get(name, {})
        if 'source' not in spec:
            self.command.error("Attribute 'source' required for import definition: {}".format(name))

        self.command.notice("Running import: {}".format(name))
        self.command.get_provider(
            'source', spec['source'], name, spec
        ).update()


    def _order_imports(self, spec, required_names, ignore_requirements):
        priorities = {}
        priority_map = {}

        if required_names is None:
            required_names = []

        def _inner_dependencies(updated_names):
            dependencies = {}

            for name, config in spec.items():
                if updated_names and name not in updated_names:
                    continue

                if config is not None and isinstance(config, dict):
                    requires = config.get('requires', None)
                    if requires:
                        require_list = ensure_list(requires)

                        if ignore_requirements:
                            dependencies[name] = intersection(require_list, updated_names, True)
                        else:
                            dependencies[name] = require_list
                    else:
                        dependencies[name] = []

            return dependencies

        if not required_names or ignore_requirements:
            dependencies = _inner_dependencies(required_names)
        else:
            while True:
                dependencies = _inner_dependencies(required_names)
                for name, requires in dependencies.items():
                    for require in requires:
                        if require not in required_names:
                            required_names.append(require)

                if len(dependencies.keys()) == len(required_names):
                    break

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
