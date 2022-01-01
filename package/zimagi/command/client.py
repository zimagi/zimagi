from .. import settings, exceptions, utility, client
from .. import codecs as shared_codecs
from . import schema, codecs, transports

import re


class Client(client.BaseAPIClient):

    def __init__(self,
        port = settings.DEFAULT_COMMAND_PORT,
        verify_cert = settings.DEFAULT_VERIFY_CERT,
        options_callback = None,
        message_callback = None,
        **kwargs
    ):
        super().__init__(
            port = port,
            decoders = [
                codecs.ZimagiJSONCodec(),  # application/vnd.zimagi+json
                shared_codecs.JSONCodec()  # application/json
            ],
            **kwargs
        )
        self.transport = transports.CommandHTTPSTransport(
            client = self,
            verify_cert = verify_cert,
            options_callback = options_callback,
            message_callback = message_callback
        )
        self.schema = self._get_schema()
        self._init_actions()

        if not self.get_status().encryption:
            self.cipher = None


    def get_status(self):
        if not getattr(self, '_status', None):
            status_url = "/".join([ self.base_url.rstrip('/'), 'status' ])

            def processor():
                return self._request(status_url)

            self._status = utility.wrap_api_call('command_status', status_url, processor)
        return self._status


    def _get_schema(self):

        def processor():
            return self._request(self.base_url)

        return utility.wrap_api_call('command_schema', self.base_url, processor)

    def _init_actions(self):
        self.actions = {}
        self.data_types = {}

        def collect_actions(link_info, parents):
            for action_name, info in link_info.items():
                if isinstance(info, schema.Link):
                    action = "/".join(parents + [ action_name ])
                    self.actions[action] = info

                    if info.resource:
                        if info.resource not in self.data_types:
                            self.data_types[info.resource] = {}
                        self.data_types[info.resource][action_name] = action
                else:
                    collect_actions(info, parents + [ action_name ])

        collect_actions(self.schema, [])


    def _normalize_action(self, action):
        return re.sub(r'(\s+|\.)', '/', action)


    def get_options(self, action):
        link = self._lookup(self._normalize_action(action))
        options = {}

        for field in link.fields:
            options[field.name] = field
        return options


    def execute(self, action, **options):
        action = self._normalize_action(action)
        action_options = utility.format_options(options)

        def processor():
            link = self._lookup(action)
            self._validate(link, action_options)
            return self._request(link.url, action_options)

        return utility.wrap_api_call('command', action, processor, action_options)


    def _get_resource_action(self, data_type, op):
        try:
            return self.data_types.get(data_type, {}).get(op, None)
        except Exception:
            raise exceptions.ClientError("There is no action for data type {} operation {}".format(data_type, op))


    def _execute_type_operation(self, data_type, op, options):
        return self.execute(
            self._get_resource_action(data_type, op),
            **options
        )

    def _execute_key_operation(self, data_type, op, key, options):
        action = self._get_resource_action(data_type, op)
        key_field = None

        for name, info in self.get_options(action).items():
            if info.required and 'key' in info.tags:
                key_field = name
                break

        if key_field is None:
            raise exceptions.ClientError("There is no key field for {} in available options".format(data_type))

        return self.execute(action, **{
            **options,
            key_field: key
        })


    def list(self, data_type, **options):
        return self._execute_type_operation(data_type, 'list', options)

    def get(self, data_type, key, **options):
        return self._execute_key_operation(data_type, 'get', key, options)

    def save(self, data_type, key, fields = None, provider = None, **options):
        action = self._get_resource_action(data_type, 'save')
        key_field = None
        provider_field = None
        fields_field = None

        for name, info in self.get_options(action).items():
            if info.required and 'key' in info.tags:
                key_field = name
            elif 'provider' in info.tags:
                provider_field = name
            elif 'fields' in info.tags:
                fields_field = name

        if key_field is None:
            raise exceptions.ClientError("There is no key field for {} in available options".format(data_type))

        options = {
            **options,
            key_field: key
        }
        if provider and provider_field:
            options[provider_field] = provider
        if fields and fields_field:
            options[fields_field] = fields

        return self.execute(action, **options)

    def remove(self, data_type, key, **options):
        return self._execute_key_operation(data_type, 'remove', key, options)

    def clear(self, data_type, **options):
        return self._execute_type_operation(data_type, 'clear', options)


    def extend(self, remote, reference, provider = None, **fields):
        fields['reference'] = reference

        options = {
            'remote': remote,
            'module_fields': fields
        }
        if provider:
            options['module_provider_name'] = provider

        return self.execute('module/add', **options)


    def run_task(self, module_name, task_name, config = None, **options):
        return self.execute('task', **{
            **options,
            'module_name': module_name,
            'task_name': task_name,
            'task_fields': config if config else {}
        })

    def run_profile(self, module_name, profile_name, config = None, components = None, **options):
        return self.execute('run', **{
            **options,
            'module_name': module_name,
            'profile_name': profile_name,
            'profile_config_fields': config if config else {},
            'profile_components': components if components else []
        })

    def destroy_profile(self, module_name, profile_name, config = None, components = None, **options):
        return self.execute('destroy', **{
            **options,
            'module_name': module_name,
            'profile_name': profile_name,
            'profile_config_fields': config if config else {},
            'profile_components': components if components else []
        })


    def run_imports(self, names = None, tags = None, **options):
        return self.execute('import', **{
            **options,
            'import_names': names if names else [],
            'tags': tags if tags else []
        })

    def run_calculations(self, names = None, tags = None, **options):
        return self.execute('calculate', **{
            **options,
            'calculation_names': names if names else [],
            'tags': tags if tags else []
        })


    def _lookup(self, action):
        node = self.schema
        found = True

        for key in action.split('/'):
            try:
                node = node[key]
            except (KeyError, IndexError, TypeError):
                found = False

        if not found or not isinstance(node, schema.Link):
            related_actions = []
            for other_action in self.actions:
                if action in other_action:
                    related_actions.append(other_action)

            raise exceptions.ParseError("Command {} does not exist.  Try one of: {}".format(
                action,
                ", ".join(related_actions)
            ))
        return node

    def _validate(self, link, options):
        provided = set(options.keys())
        required = set([
            field.name for field in link.fields if field.required
        ])
        optional = set([
            field.name for field in link.fields if not field.required
        ])
        errors = {}

        missing = required - provided
        for item in missing:
            errors[item] = 'Parameter is required'

        unexpected = provided - (optional | required)
        for item in unexpected:
            errors[item] = 'Unknown parameter'

        if errors:
            raise exceptions.ParseError(errors)
