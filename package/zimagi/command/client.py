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
        if not self.get_status().encryption:
            self.cipher = None

        self.schema = self.get_schema()
        self._init_actions()


    def _init_actions(self):
        self.actions = {}

        def collect_actions(link_info, parents):
            for action_name, info in link_info.items():
                if isinstance(info, schema.Link):
                    action = "/".join(parents + [ action_name ])
                    self.actions[action] = info
                else:
                    collect_actions(info, parents + [ action_name ])

        collect_actions(self.schema, [])


    def _normalize_action(self, action):
        return re.sub(r'(\s+|\.)', '/', action)


    def execute(self, action, **options):
        action = self._normalize_action(action)
        action_options = utility.format_options('POST', options)
        link = self._lookup(action)

        def validate(url, params):
            self._validate(link, params)

        def processor():
            return self._request('POST', link.url, action_options,
                validate_callback = validate
            )
        return utility.wrap_api_call('command', action, processor, action_options)


    def extend(self, remote, reference, provider = None, **fields):
        fields['reference'] = reference

        options = {
            'remote': remote,
            'module_fields': fields
        }
        if provider:
            options['module_provider_name'] = provider

        return self.execute('module/add', **options)


    def run_task(self, module_key, task_name, config = None, **options):
        return self.execute('task', **{
            **options,
            'module_key': module_key,
            'task_key': task_name,
            'task_fields': config if config else {}
        })

    def run_profile(self, module_key, profile_key, config = None, components = None, **options):
        return self.execute('run', **{
            **options,
            'module_key': module_key,
            'profile_key': profile_key,
            'profile_config_fields': config if config else {},
            'profile_components': components if components else []
        })

    def destroy_profile(self, module_key, profile_key, config = None, components = None, **options):
        return self.execute('destroy', **{
            **options,
            'module_key': module_key,
            'profile_key': profile_key,
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
