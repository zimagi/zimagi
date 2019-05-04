from .base import ParserBase
from utility.data import get_dict_combinations, normalize_index

import re
import copy


class ReferenceParser(ParserBase):

    reference_pattern = r'^\&\{?(?:([\+\!]+))?([a-z][\_a-z]+)(?:\(([^\)]+)\))?\:([^\:]+)\:([^\[\s]+)(?:\[(.+)\])?\}?$'
    reference_value_pattern = r'(?<!\&)\&\{?((?:[\+\!]+)?[a-z][\_a-z]+(?:\([^\)]+\))?\:[^\:]+\:[^\[\s\}]+(?:\[[^\]]+\])?)[\}\s]?'


    def parse(self, value):
        if not isinstance(value, str):
            return value

        if re.search(self.reference_pattern, value):
            value = self.parse_reference(value)
        else:
            for ref_match in re.finditer(self.reference_value_pattern, value):
                reference_value = self.parse_reference("&{}".format(ref_match.group(1)))
                if isinstance(reference_value, (list, tuple)):
                    reference_value = ",".join(reference_value)
                elif isinstance(reference_value, dict):
                    reference_value = json.dumps(reference_value)

                value = value.replace(ref_match.group(0), reference_value)
        return value

    def parse_reference(self, value):
        ref_match = re.search(self.reference_pattern, value)
        operations = ref_match.group(1)
        if operations:
            operations = operations.strip()
        else:
            operations = ''

        facade = ref_match.group(2)
        facade = copy.deepcopy(self.command.manager.get_facade_index()[facade])

        scopes = ref_match.group(3)
        scope_filters = {}
        if scopes:
            for scope_filter in scopes.replace(' ', '').split(';'):
                scope_field, scope_value = scope_filter.split('=')
                scope_filters[scope_field] = scope_value.replace(' ', '').split(',')
            scopes = get_dict_combinations(scope_filters)
        else:
            scopes = []
        scope_filters = facade.scope_name_filters()

        names = ref_match.group(4)
        if names:
            search_names = names.replace(' ', '').split(',')
            names = []
            for name in search_names:
                if name[-1] == '*':
                    keys = facade.keys(name__startswith = name[:-1])
                    names.extend(set(keys))
                elif name[0] == '*':
                    keys = facade.keys(name__endswith = name[1:])
                    names.extend(set(keys))
                else:
                    names.append(name)

        field = ref_match.group(5)
        keys = ref_match.group(6)
        if keys:
            keys = keys.replace(' ', '').split('][')

        def _set_instance_values(values):
            instances = list(facade.query(name__in = names))
            for instance in self.command.get_instances(facade, objects = instances):
                instance_value = getattr(instance, field, None)
                if instance_value is not None:
                    if isinstance(instance_value, (dict, list, tuple)) and keys:
                        def _get_value(data, key_list):
                            if isinstance(data, (dict, list, tuple)) and len(key_list):
                                base_key = normalize_index(key_list.pop(0))
                                try:
                                    return _get_value(data[base_key], key_list)
                                except Exception:
                                    return None
                            return data

                        values.append(_get_value(instance_value, keys))
                    else:
                        values.append(instance_value)

        instance_values = []
        if scopes:
            for scope in scopes:
                filters = {}
                for scope_key, scope_value in scope.items():
                    filters[scope_filters[scope_key]] = scope_value

                facade.set_scope(filters)
                _set_instance_values(instance_values)
        else:
            _set_instance_values(instance_values)

        if '!' in operations:
            instance_values = list(set(instance_values))

        if '+' in operations or len(instance_values) > 1:
            return instance_values
        elif len(instance_values) == 1:
            return instance_values[0]
        return None
