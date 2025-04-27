from utility.data import ensure_list
from utility.python import create_class

from ..helpers import get_facade, get_fields, get_joined_value, parse_fields


def SaveCommand(parents, base_name, facade_name, provider_name=None, edit_roles=None, save_fields=None):
    if save_fields is None:
        save_fields = {}

    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name)
    _key_field = get_joined_value(base_name, "key")
    _fields_field = get_joined_value(base_name, "fields")

    def __get_priority(self):
        return 15

    def __get_run_background(self):
        return False

    def __groups_allowed(self):
        from settings.roles import Roles

        return [Roles.admin] + ensure_list(edit_roles)

    def __parse(self, add_api_fields=False):
        facade = getattr(self, _facade_name)
        key_options = {}

        if provider_name:
            self.parse_test()
            self.parse_force()
            getattr(self, f"parse_{provider_name}_provider_name")("--provider")

        from data.base.id_resource import IdentifierResourceBase

        if issubclass(facade.model, IdentifierResourceBase) and facade.key() == facade.pk:
            key_options["optional"] = "--id"

        getattr(self, f"parse_{_key_field}")(**key_options)

        if not save_fields:
            help_callback = self.get_provider(provider_name, "help").field_help if provider_name else None
            getattr(self, f"parse_{_fields_field}")(True, help_callback)
        else:
            parse_fields(self, save_fields)

        self.parse_relations(facade)

    def __exec(self):
        facade = getattr(self, _facade_name)

        key = getattr(self, _key_field)
        if save_fields:
            fields = get_fields(self, save_fields)
        else:
            fields = getattr(self, _fields_field)

        provider_type = None
        if provider_name:
            if self.get_instance(facade, key, required=False):
                if getattr(self, f"check_{provider_name}_provider_name")():
                    provider_type = getattr(self, f"{provider_name}_provider_name", None)
            else:
                provider_type = getattr(self, f"{provider_name}_provider_name", None)

        self.save_instance(
            facade,
            key,
            fields={**self.set_scope(facade), **self.get_relations(facade), **fields, "provider_type": provider_type},
        )

    def __str__(self):
        return f"Save <{base_name}>"

    attributes = {
        "_resource": facade_name,
        "get_priority": __get_priority,
        "get_run_background": __get_run_background,
        "parse": __parse,
        "exec": __exec,
        "__str__": __str__,
    }
    if edit_roles:
        attributes["groups_allowed"] = __groups_allowed

    return create_class(f"commands.{facade_name}.save", "SaveCommand", parents=_parents, attributes=attributes)
