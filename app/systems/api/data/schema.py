import re
from functools import lru_cache
from urllib.parse import urljoin

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions
from rest_framework.schemas.openapi import AutoSchema, SchemaGenerator

from .filter.backends import RelatedFilterBackend


def get_csv_response_schema(description):
    return {"200": {"content": {"text/csv": {"schema": {}}}, "description": description}}


class DataSchemaGenerator(SchemaGenerator):
    def has_view_permissions(self, path, method, view):
        if view.request is None:
            return True
        try:
            view.check_permissions(view.request)
        except (exceptions.APIException, Http404, PermissionDenied):
            return False
        return True

    def get_schema(self, request=None, public=False):
        paths, data, components = self.get_path_info(request=request, public=public, full=False)
        return {"openapi": "3.1.0", "info": self.get_info(), "paths": paths, "components": components, "x-data": data}

    def get_info(self):
        info = {"title": self.title or "", "version": self.version or ""}
        if self.description is not None:
            info["description"] = self.description

        return info

    def get_path_info(self, search_path=None, request=None, public=False, full=False):
        paths = {}
        data = {}
        components = {"schemas": {}}

        self._initialise_endpoints()
        _, view_endpoints = self._get_paths_and_endpoints(None if public else request)

        for path, method, view in view_endpoints:
            if path != "/status/":
                url_path = path.replace("{", "").replace("}", "")
                if not search_path or (
                    url_path.strip("/") == search_path.strip("/") and self.has_view_permissions(path, method, view)
                ):
                    components["schemas"].update(view.schema.get_components(path, method))

                    if path.startswith("/"):
                        path = path[1:]
                    path = urljoin(self.url or "/", path)

                    if getattr(view, "facade", None):
                        if view.facade.name not in data:
                            data[view.facade.name] = self.get_data_info(view.facade)

                    if full:
                        if path not in paths:
                            paths[path] = {}

                        paths[path][method.lower()] = view.schema.get_operation(path, method)

                    elif request and path not in paths:
                        url_path = path.replace("{", "").replace("}", "")
                        paths[path] = {
                            "$ref": "{}/schema/{}".format(request.build_absolute_uri().rstrip("/"), url_path.lstrip("/"))
                        }

        self.check_duplicate_operation_id(paths)

        if search_path and len(paths) > 0:
            paths = paths[list(paths.keys())[0]]
        return paths, data, components

    def get_data_info(self, facade):
        scope_fields = {}
        for field_name, field_info in facade.get_scope_relations().items():
            scope_fields[field_name] = field_info["model"].facade.name

        relation_fields = {}
        for field_name, field_info in facade.get_extra_relations().items():
            relation_fields[field_name] = field_info["model"].facade.name

        reverse_fields = {}
        for field_name, field_info in facade.get_reverse_relations().items():
            reverse_fields[field_name] = field_info["model"].facade.name

        return {
            "id": facade.pk,
            "key": facade.key(),
            "system": [field.name for field in facade.system_field_instances],
            "unique": facade.unique_fields,
            "dynamic": facade.dynamic_fields,
            "atomic": facade.atomic_fields,
            "scope": scope_fields,
            "relations": relation_fields,
            "reverse": reverse_fields,
        }


class PathSchema(AutoSchema):
    def get_operation_id_base(self, path, method, action):
        return "PathSchema"

    def get_responses(self, path, method):
        return {"200": {"content": {"application/json": {"schema": {}}}, "description": "Path OpenAPI Schema definition"}}


class DataSetSchema(AutoSchema):
    def get_operation_id_base(self, path, method, action):
        return "DataSetCSV"

    def get_responses(self, path, method):
        return get_csv_response_schema("CSV download of dataset data")


class DataSchema(AutoSchema):
    def allows_filters(self, path, method):
        if getattr(self.view, "filter_backends", None) is None:
            return False

        if hasattr(self.view, "action"):
            return self.view.action in ["list", "values", "count", "csv", "json", "retrieve", "create", "update", "destroy"]
        return method.lower() in ["get", "put", "delete"]

    def get_component_name(self, serializer):
        if self.component_name is not None:
            return self.component_name

        component_name = serializer.__class__.__name__.replace("_", "")
        pattern = re.compile("serializer", re.IGNORECASE)
        component_name = pattern.sub("", component_name)

        if component_name == "":
            raise Exception(
                '"{}" is an invalid class name for schema generation. '
                'Serializer\'s class name should be unique and explicit. e.g. "ItemSerializer"'.format(
                    serializer.__class__.__name__
                )
            )

        return component_name

    @lru_cache(maxsize=None)
    def get_filter_parameters(self, path, method):
        if not self.allows_filters(path, method):
            return []

        def check_filter_overlap(data_types):
            if len(data_types) <= 2:
                return False
            if len(data_types) != len(set(data_types)):
                return True
            return False

        def load_parameters(view, name_prefix="", depth=1, data_types=None):
            parents = list(view.facade.get_parent_relations().keys())
            relations = view.facade.get_all_relations()
            parameters = []
            id_map = {}

            for filter_backend in view.get_filter_classes():
                if depth == 1 or filter_backend == RelatedFilterBackend:
                    for parameter in filter_backend().get_schema_operation_parameters(view):
                        field_name = parameter["name"]

                        if field_name not in id_map:
                            nested_name = f"{name_prefix}__{field_name}" if name_prefix else field_name
                            base_name = (
                                parameter["schema"]["x-base-field"] if "x-base-field" in parameter["schema"] else field_name
                            )

                            if field_name in relations:
                                related_view = relations[field_name]["model"].facade.get_viewset()(action=self.view.action)
                                if not check_filter_overlap([*parents, *data_types, related_view.facade.name]):
                                    parameters.extend(
                                        load_parameters(
                                            related_view,
                                            nested_name,
                                            depth=(depth + 1),
                                            data_types=[*parents, *data_types, related_view.facade.name],
                                        )
                                    )
                            else:
                                add_filter = True

                                if base_name in relations:
                                    related_view = relations[base_name]["model"].facade.get_viewset()(
                                        action=self.view.action
                                    )
                                    if check_filter_overlap([*parents, *data_types, related_view.facade.name]):
                                        add_filter = False

                                if add_filter:
                                    parameter["name"] = nested_name

                                    if "x-field" in parameter["schema"]:
                                        parameter["schema"]["x-field"] = "{}{}".format(
                                            f"{name_prefix}__" if name_prefix else "", parameter["schema"]["x-field"]
                                        )
                                        if name_prefix:
                                            parameter["schema"]["x-relation"] = name_prefix

                                    parameters.append(parameter)

                            id_map[field_name] = True
            return parameters

        return load_parameters(self.view, data_types=[self.view.facade.name])

    @lru_cache(maxsize=None)
    def get_responses(self, path, method):
        if self.view.action == "csv":
            return get_csv_response_schema("CSV download of field data")
        else:
            responses = super().get_responses(path, method)

            if self.view.action in ("json",):
                for status_code, response in responses.items():
                    for format, info in response["content"].items():
                        response["content"][format]["schema"] = {"type": "array", "items": {}}
            return responses
