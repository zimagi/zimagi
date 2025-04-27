import os
import re
import threading
from collections import OrderedDict

import oyaml
from systems.commands.index import CommandMixin
from systems.manage.template import TemplateException
from utility.data import Collection, deep_merge, ensure_list, normalize_value
from utility.filesystem import create_dir, load_file, load_yaml, save_file


class ModuleMixin(CommandMixin("module")):
    template_lock = threading.Lock()

    def provision_template(self, module, package_name, template_fields, display_only=False):
        module.initialize(self)
        self.manager.load_templates()

        index, template_fields = self._load_package(package_name, template_fields, display_only)
        with self.template_lock:
            self._store_template_map(module, index, template_fields, display_only)
            self._create_template_directories(module, index, display_only)

        self._run_package_commands(index, display_only)

    def _load_package(self, package_name, template_fields, display_only):
        template_fields = self._prepare_template_fields(
            self._load_package_index(package_name, template_fields),
            normalize_value(template_fields, strip_quotes=True, parse_json=True),
            display_only,
        )
        return self._load_package_index(package_name, template_fields), template_fields

    def _load_package_index(self, package_name, template_fields):
        index_config = oyaml.safe_load(self._render_package_template(package_name, "index.yml", template_fields))
        index_config["name"] = package_name
        return Collection(**index_config)

    def _prepare_template_fields(self, index, template_fields, display_only):
        processed_fields = OrderedDict()

        for field, info in index.variables.items():
            if info.get("required", False) and field not in template_fields:
                if display_only:
                    template_fields[field] = f"<{{{field}}}>"
                else:
                    raise TemplateException(f"Field {field} is required for template {index.name}")

            if field in template_fields:
                processed_fields[field] = template_fields[field]

            elif info.get("default", None) is not None:
                processed_fields[field] = normalize_value(info["default"], strip_quotes=True, parse_json=True)
            else:
                processed_fields[field] = None

        return processed_fields

    def _store_template_map(self, module, index, template_fields, display_only):
        self.notice("Template variables:")
        self.table(
            [["Variable", "Value", "Help"]]
            + [[key, value, index.variables[key].get("help", "NA")] for key, value in template_fields.items()],
            "variables",
        )
        self.spacing()

        for path, info in index.map.items():
            target = None

            if isinstance(info, str):
                target = info
                info = {}

            elif info.get("when", True) and "target" in info:
                target = info["target"]

            if target:
                path_components = os.path.split(self.manager.get_module_path(module, target))
                target_path = os.path.join(*path_components)

                if info.get("template", True):
                    file_content = self._render_package_template(index.name, path, template_fields)
                else:
                    file_content = load_file(self.manager.get_template_path(index.name, path))

                if info.get("location", None) and path.endswith(".yml"):
                    file_data = normalize_value(load_yaml(target_path), strip_quotes=True, parse_json=True)

                    location = info["location"].split(".")
                    embed_data = normalize_value(oyaml.safe_load(file_content), strip_quotes=True, parse_json=True)
                    merge_data = {}
                    iter_data = merge_data

                    for index, key in enumerate(location):
                        if (index + 1) == len(location):
                            iter_data[key] = embed_data
                        else:
                            iter_data[key] = {}

                        iter_data = iter_data[key]

                    file_content = oyaml.dump(deep_merge(file_data, merge_data))

                self.data("Path", path, "path")
                self.data("Target", target, "target")
                if info.get("location", None):
                    self.data("location", info["location"], "location")
                self.notice("-" * self.display_width)
                if info.get("template", True):
                    self.info(file_content)
                self.spacing()

                if not display_only:
                    create_dir(path_components[0])

                    permissions = str(info["permissions"]) if info.get("permissions", None) else None
                    save_file(target_path, file_content, permissions=permissions)

    def _render_package_template(self, package_name, file_path, template_fields):
        template = self.manager.template_engine.get_template(os.path.join(package_name, file_path))
        return template.render(**template_fields)

    def _create_template_directories(self, module, index, display_only):
        module_path = self.manager.get_module_path(module)

        if index.directories:
            self.notice("Directories:")
            self.spacing()
            for directory in ensure_list(index.directories):
                module_dir = os.path.join(module_path, directory)
                self.info(module_dir)
                if not display_only:
                    create_dir(module_dir)
            self.spacing()

    def _run_package_commands(self, index, display_only):
        if index.commands:
            for command in ensure_list(index.commands):
                if isinstance(command, str):
                    command = re.split(r"\s+", command)

                self.data("Command", " ".join(command), "command")
                self.notice("-" * self.display_width)
                if not display_only:
                    if not self.sh(command):
                        raise TemplateException(f"Template package command execution failed: {command}")
            self.spacing()
