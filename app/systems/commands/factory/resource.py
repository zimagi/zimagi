from utility.data import ensure_list

from .operations import clear, get, list, remove, save


def ResourceCommandSet(
    command,
    parents,
    base_name,
    facade_name,
    provider_name=None,
    save_fields=None,
    edit_roles=None,
    view_roles=None,
    allow_list=True,
    allow_access=True,
    allow_update=True,
    allow_remove=True,
    allow_clear=True,
):
    if save_fields is None:
        save_fields = {}

    if edit_roles:
        edit_roles = ensure_list(edit_roles)
        if view_roles:
            view_roles = ensure_list(view_roles) + edit_roles
        else:
            view_roles = edit_roles

    if allow_list:
        command["list"] = list.ListCommand(parents, base_name, facade_name, view_roles=view_roles)
    if allow_access:
        command["get"] = get.GetCommand(parents, base_name, facade_name, view_roles=view_roles)
    if allow_update:
        command["save"] = save.SaveCommand(
            parents, base_name, facade_name, provider_name=provider_name, edit_roles=edit_roles, save_fields=save_fields
        )
    if allow_remove:
        command["remove"] = remove.RemoveCommand(parents, base_name, facade_name, edit_roles=edit_roles)
        if allow_clear:
            command["clear"] = clear.ClearCommand(parents, base_name, facade_name, edit_roles=edit_roles)
    return command
