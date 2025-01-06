import inflect
from django.conf import settings


class MetaBaseMixin(type):
    def __new__(cls, name, bases, attr):
        cls.pluralizer = inflect.engine()

        if "schema" in attr:
            for base_name, info in attr["schema"].items():
                facade_name = info.get("data", None)

                cls._key_methods(attr, base_name, facade_name, info)
                cls._fields_methods(attr, base_name, facade_name, info)

                if facade_name:
                    if "model" in info and getattr(settings, "DB_LOCK", None):
                        cls._facade_methods(attr, base_name, facade_name, info["model"])
                        cls._search_methods(attr, base_name, facade_name, info)

                    if info.get("provider", False):
                        cls._provider_methods(attr, base_name, facade_name, info)

                    if info.get("relations", False):
                        cls._relation_methods(attr, base_name, facade_name)

        return super().__new__(cls, name, bases, attr)

    @classmethod
    def _facade_methods(cls, _methods, _name, _facade_name, _model_cls):
        def __facade(self):
            return self.facade(_model_cls.facade)

        def __parse_scope(self):
            facade = self.facade(_model_cls.facade)
            self.parse_scope(facade)

        def __set_scope(self, optional=False):
            facade = self.facade(_model_cls.facade)
            self.set_scope(facade, optional)

        def __parse_relations(self):
            facade = self.facade(_model_cls.facade)
            self.parse_relations(facade)

        def __get_relations(self):
            facade = self.facade(_model_cls.facade)
            return self.get_relations(facade)

        _methods[f"_{_facade_name}"] = property(__facade)
        _methods[f"parse_{_name}_scope"] = __parse_scope
        _methods[f"set_{_name}_scope"] = __set_scope
        _methods[f"parse_{_name}_relations"] = __parse_relations
        _methods[f"get_{_name}_relations"] = __get_relations

    @classmethod
    def _provider_methods(cls, _methods, _name, _facade_name, _info):
        _provider_name = f"{_name}_provider_name"
        _provider = f"{_name}_provider"

        if "model" in _info and getattr(settings, "DB_LOCK", None):
            _full_name = _info["model"].facade.name
        else:
            _full_name = _name

        _default = _info.get("default", "base")
        _help_text = f"system {_full_name} provider"

        def __parse_provider_name(self, optional="--provider", help_text=_help_text, tags=None):
            if not tags:
                tags = ["provider"]

            self.parse_variable(_provider_name, optional, str, help_text, value_label="NAME", default=_default, tags=tags)

        def __check_provider_name(self):
            return self.options.get(_provider_name) != _default

        def __provider_name(self):
            name = self.options.get(_provider_name)
            return _default if name is None else name

        def __provider(self):
            return self.get_provider(_name, getattr(self, _provider_name))

        _methods[f"parse_{_provider_name}"] = __parse_provider_name
        _methods[f"check_{_provider_name}"] = __check_provider_name
        _methods[_provider_name] = property(__provider_name)
        _methods[_provider] = property(__provider)

    @classmethod
    def _key_methods(cls, _methods, _name, _facade_name, _info):
        _instance_id = f"{_name}_id"
        _instance_key = f"{_name}_key"
        _instance_keys = f"{_name}_keys"

        if "model" in _info and getattr(settings, "DB_LOCK", None):
            _facade = _info["model"].facade
            _plural = _facade.plural
            _full_name = _facade.name
        else:
            _plural = cls.pluralizer.plural(_name)
            _full_name = _name

        _default = _info.get("key_default", None)
        _help_text = f"{_full_name} key"
        _multi_help_text = f"one or more {_help_text}s"

        def __parse_id(self, optional=False, help_text=_help_text, tags=None):
            default = None

            if not tags:
                tags = ["key"]

            if _default:
                value = getattr(self, _default, None)
                default = value if value is not None else _default

            self.parse_variable(_instance_id, optional, str, help_text, value_label="KEY", default=default, tags=tags)

        def __id(self):
            return self.options.get(_instance_id)

        def __check_id(self):
            default = None

            if _default:
                value = getattr(self, _default, None)
                default = value if value is not None else _default

            if default is None:
                return self.options.get(_instance_id) is not None

            return self.options.get(_instance_id) != default

        def __parse_key(self, optional=False, help_text=_help_text, tags=None):
            default = None

            if not tags:
                tags = ["key"]

            if "model" in _info and getattr(settings, "DB_LOCK", None):
                facade = getattr(self, f"_{_facade_name}")
                self.parse_scope(facade)

            if _default:
                value = getattr(self, _default, None)
                default = value if value is not None else _default

            self.parse_variable(_instance_key, optional, str, help_text, value_label="KEY", default=default, tags=tags)

        def __key(self):
            return self.options.get(_instance_key)

        def __check_key(self):
            default = None

            if _default:
                value = getattr(self, _default, None)
                default = value if value is not None else _default

            if default is None:
                return self.options.get(_instance_key) is not None

            return self.options.get(_instance_key) != default

        def __parse_keys(self, optional=f"--{_plural}", help_text=_multi_help_text, tags=None):
            if not tags:
                tags = ["key", "keys"]

            if "model" in _info and getattr(settings, "DB_LOCK", None):
                facade = getattr(self, f"_{_facade_name}")
                self.parse_scope(facade)

            self.parse_variables(_instance_keys, optional, str, help_text, value_label="KEY", default=[], tags=tags)

        def __keys(self):
            return self.options.get(_instance_keys)

        def __check_keys(self):
            keys = self.options.get(_instance_keys)
            return len(keys) > 0 if isinstance(keys, (list, tuple)) else False

        def __accessor(self):
            facade = getattr(self, f"_{_facade_name}")
            key = getattr(self, _instance_key)
            if key:
                self.set_scope(facade)
                return self.get_instance(facade, key)

            id = getattr(self, _instance_id)
            if id:
                return self.get_instance_by_id(facade, id)

            return None

        _methods[f"parse_{_instance_id}"] = __parse_id
        _methods[f"check_{_instance_id}"] = __check_id
        _methods[_instance_id] = property(__id)

        _methods[f"parse_{_instance_key}"] = __parse_key
        _methods[f"check_{_instance_key}"] = __check_key
        _methods[_instance_key] = property(__key)

        _methods[f"parse_{_instance_keys}"] = __parse_keys
        _methods[f"check_{_instance_keys}"] = __check_keys
        _methods[_instance_keys] = property(__keys)

        if "model" in _info and getattr(settings, "DB_LOCK", None):
            _methods[_name] = property(__accessor)

    @classmethod
    def _fields_methods(cls, _methods, _name, _facade_name, _info):
        _instance_fields = f"{_name}_fields"

        def __parse_fields(self, optional=True, help_callback=None, exclude_fields=None, tags=None):
            if not tags:
                tags = ["fields"]

            facade = getattr(self, f"_{_facade_name}") if "model" in _info else None
            self.parse_fields(
                facade,
                _instance_fields,
                optional=optional,
                help_callback=help_callback,
                callback_args=[_name],
                exclude_fields=exclude_fields,
                tags=tags,
            )

        def __fields(self):
            return self.options.get(_instance_fields)

        _methods[f"parse_{_instance_fields}"] = __parse_fields
        _methods[_instance_fields] = property(__fields)

    @classmethod
    def _relation_methods(cls, _methods, _name, _facade_name):
        if getattr(settings, "DB_LOCK", None):
            facade = settings.MANAGER.index.get_facade_index()[_facade_name]
            for field_name, info in facade.get_extra_relations().items():
                cls._key_methods(_methods, field_name, info["model"].facade.name, info)

    @classmethod
    def _search_methods(cls, _methods, _name, _facade_name, _info):
        _instance_search = f"{_name}_search"
        _instance_search_or = f"{_instance_search}_or"
        _instance_search_joiner = f"{_instance_search}_joiner"
        _instance_order = f"{_name}_order"
        _instance_limit = f"{_name}_limit"
        _instance_count = f"{_name}_count"

        if "model" in _info and getattr(settings, "DB_LOCK", None):
            _full_name = _info["model"].facade.name
        else:
            _full_name = _name

        _search_help_text = f"{_full_name} search filters"
        _order_help_text = f"{_full_name} ordering fields (~field for desc)"
        _limit_help_text = f"{_full_name} result limit"
        _count_help_text = f"{_full_name} result count"

        def __parse_search(self, optional=True, help_text=_search_help_text, tags=None):
            if not tags:
                tags = ["list", "search"]

            if "model" in _info and getattr(settings, "DB_LOCK", None):
                facade = getattr(self, f"_{_facade_name}")
                self.parse_scope(facade)

            self.parse_variables(_instance_search, optional, str, help_text, value_label="REFERENCE", default=[], tags=tags)
            self.parse_flag(_instance_search_or, "--or", "perform an OR query on input filters", tags=tags)

        def __search(self):
            return self.options.get(_instance_search)

        def __search_joiner(self):
            return "OR" if self.options.get(_instance_search_or) else "AND"

        def __parse_order(self, optional="--order", help_text=_order_help_text, tags=None):
            if not tags:
                tags = ["list", "ordering"]

            self.parse_variables(_instance_order, optional, str, help_text, value_label="[~]FIELD", default=[], tags=tags)

        def __order(self):
            return self.options.get(_instance_order)

        def __parse_limit(self, optional="--limit", help_text=_limit_help_text, tags=None):
            if not tags:
                tags = ["list", "limit"]

            self.parse_variable(_instance_limit, optional, int, help_text, value_label="NUM", default=100, tags=tags)

        def __limit(self):
            return int(self.options.get(_instance_limit))

        def __parse_count(self, help_text=_count_help_text, tags=None):
            if not tags:
                tags = ["list", "count"]

            self.parse_flag(_instance_count, "--count", help_text, tags=tags)

        def __count(self):
            return int(self.options.get(_instance_count))

        def __instances(self):
            facade = getattr(self, f"_{_facade_name}")
            search = getattr(self, _instance_search)
            joiner = getattr(self, _instance_search_joiner)

            self.set_scope(facade)
            return self.search_instances(facade, search, joiner)

        _methods[f"parse_{_instance_search}"] = __parse_search
        _methods[_instance_search] = property(__search)
        _methods[_instance_search_joiner] = property(__search_joiner)
        _methods[f"parse_{_instance_order}"] = __parse_order
        _methods[_instance_order] = property(__order)
        _methods[f"parse_{_instance_limit}"] = __parse_limit
        _methods[_instance_limit] = property(__limit)
        _methods[f"parse_{_instance_count}"] = __parse_count
        _methods[_instance_count] = property(__count)

        if "model" in _info and getattr(settings, "DB_LOCK", None):
            _methods[f"{_name}_instances"] = property(__instances)
