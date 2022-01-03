from django.conf import settings


class MetaBaseMixin(type):

    def __new__(cls, name, bases, attr):
        if 'schema' in attr:
            for base_name, info in attr['schema'].items():
                facade_name = info.get('data', None)

                if facade_name:
                    if 'model' in info:
                        cls._facade_methods(attr, base_name, facade_name, info['model'])
                        cls._search_methods(attr, base_name, facade_name, info)

                    cls._fields_methods(attr, base_name, facade_name, info)

                    if info.get('provider', False):
                        cls._provider_methods(attr, base_name, facade_name, info)

                    if info.get('relations', False):
                        cls._relation_methods(attr, base_name, facade_name, info)

                cls._name_methods(attr, base_name, facade_name, info)

        return super().__new__(cls, name, bases, attr)


    @classmethod
    def _facade_methods(cls, _methods, _name, _facade_name, _model_cls):
        def __facade(self):
            return self.facade(_model_cls.facade)

        def __parse_scope(self):
            facade = self.facade(_model_cls.facade)
            self.parse_scope(facade)

        def __set_scope(self, optional = False):
            facade = self.facade(_model_cls.facade)
            self.set_scope(facade, optional)

        def __parse_relations(self):
            facade = self.facade(_model_cls.facade)
            self.parse_relations(facade)

        def __get_relations(self):
            facade = self.facade(_model_cls.facade)
            return self.get_relations(facade)

        _methods["_{}".format(_facade_name)] = property(__facade)
        _methods["parse_{}_scope".format(_name)] = __parse_scope
        _methods["set_{}_scope".format(_name)] = __set_scope
        _methods["parse_{}_relations".format(_name)] = __parse_relations
        _methods["get_{}_relations".format(_name)] = __get_relations


    @classmethod
    def _provider_methods(cls, _methods, _name, _facade_name, _info):
        _provider_name = "{}_provider_name".format(_name)
        _provider = "{}_provider".format(_name)

        _provider_config = _info.get('provider_config', True)

        if 'model' in _info:
            _full_name = _info['model'].facade.name
        else:
            _full_name = _name

        _default = _info.get('default', 'base')
        _help_text = 'system {} provider'.format(
            _full_name
        )

        def __parse_provider_name(self, optional = '--provider', help_text = _help_text, tags = None):
            if not tags:
                tags = ['provider']

            self.parse_variable(_provider_name, optional, str, help_text,
                value_label = 'NAME',
                default = _default,
                tags = tags
            )

        def __check_provider_name(self):
            return self.options.get(_provider_name) != _default

        def __provider_name(self):
            return self.options.get(_provider_name)

        def __provider(self):
            return self.get_provider(_name, getattr(self, _provider_name))

        _methods["parse_{}".format(_provider_name)] = __parse_provider_name
        _methods["check_{}".format(_provider_name)] = __check_provider_name
        _methods[_provider_name] = property(__provider_name)
        _methods[_provider] = property(__provider)


    @classmethod
    def _name_methods(cls, _methods, _name, _facade_name, _info):
        _instance_name = "{}_name".format(_name)
        _instance_names = "{}_names".format(_name)

        if 'model' in _info:
            _facade = _info['model'].facade
            _plural = _facade.plural
            _full_name = _facade.name
        else:
            _plural = "{}s".format(_name)
            _full_name = _name

        _default = _info.get('name_default', None)
        _help_text = "{} name".format(_full_name)
        _multi_help_text = "one or more {}s".format(_help_text)

        def __parse_name(self, optional = False, help_text = _help_text, tags = None):
            default = None

            if not tags:
                tags = ['key']

            if 'model' in _info:
                facade = getattr(self, "_{}".format(_facade_name))
                self.parse_scope(facade)

            if _default:
                value = getattr(self, _default, None)
                if value is not None:
                    default = value
                else:
                    default = _default

            self.parse_variable(_instance_name, optional, str, help_text,
                value_label = 'NAME',
                default = default,
                tags = tags
            )

        def __name(self):
            return self.options.get(_instance_name)

        def __check_name(self):
            default = None

            if _default:
                value = getattr(self, _default, None)
                if value is not None:
                    default = value
                else:
                    default = _default

            if default is None:
                return self.options.get(_instance_name) is not None

            return self.options.get(_instance_name) != default

        def __parse_names(self, optional = "--{}".format(_plural), help_text = _multi_help_text, tags = None):
            if not tags:
                tags = ['key', 'keys']

            self.parse_variables(_instance_names, optional, str, help_text,
                value_label = 'NAME',
                default = [],
                tags = tags
            )

        def __names(self):
            return self.options.get(_instance_names)

        def __check_names(self):
            return len(self.options.get(_instance_names, [])) > 0

        def __accessor(self):
            facade = getattr(self, "_{}".format(_facade_name))
            name = getattr(self, _instance_name)

            self.set_scope(facade)
            return self.get_instance(facade, name)

        _methods["parse_{}".format(_instance_name)] = __parse_name
        _methods["check_{}".format(_instance_name)] = __check_name
        _methods[_instance_name] = property(__name)

        _methods["parse_{}".format(_instance_names)] = __parse_names
        _methods["check_{}".format(_instance_names)] = __check_names
        _methods[_instance_names] = property(__names)

        if 'model' in _info:
            _methods[_name] = property(__accessor)


    @classmethod
    def _fields_methods(cls, _methods, _name, _facade_name, _info):
        _instance_fields = "{}_fields".format(_name)

        if 'model' in _info:
            _facade = _info['model'].facade
            _full_name = _facade.name
        else:
            _full_name = _name

        _help_text = "{} fields".format(_full_name)

        def __parse_fields(self, optional = True, help_callback = None, exclude_fields = None, tags = None):
            if not tags:
                tags = ['fields']

            facade = getattr(self, "_{}".format(_facade_name)) if 'model' in _info else None
            self.parse_fields(facade, _instance_fields,
                optional = optional,
                help_callback = help_callback,
                callback_args = [_name],
                exclude_fields = exclude_fields,
                tags = tags
            )

        def __fields(self):
            return self.options.get(_instance_fields, {})

        _methods["parse_{}".format(_instance_fields)] = __parse_fields
        _methods[_instance_fields] = property(__fields)


    @classmethod
    def _relation_methods(cls, _methods, _name, _facade_name, _info):
        facade = settings.MANAGER.index.get_facade_index()[_facade_name]
        for field_name, info in facade.get_relations().items():
            cls._name_methods(_methods, field_name, _facade_name, info)



    @classmethod
    def _search_methods(cls, _methods, _name, _facade_name, _info):
        _instance_search = "{}_search".format(_name)
        _instance_search_or = "{}_or".format(_instance_search)
        _instance_search_joiner = "{}_joiner".format(_instance_search)
        _instance_order = "{}_order".format(_name)
        _instance_limit = "{}_limit".format(_name)

        if 'model' in _info:
            _full_name = _info['model'].facade.name
        else:
            _full_name = _name

        _search_help_text = "{} search filters".format(_full_name)
        _order_help_text = "{} ordering fields (~field for desc)".format(_full_name)
        _limit_help_text = "{} result limit".format(_full_name)

        def __parse_search(self, optional = True, help_text = _search_help_text, tags = None):
            if not tags:
                tags = ['list', 'search']

            if 'model' in _info:
                facade = getattr(self, "_{}".format(_facade_name))
                self.parse_scope(facade)

            self.parse_variables(_instance_search, optional, str, help_text,
                value_label = 'REFERENCE',
                default = [],
                tags = tags
            )
            self.parse_flag(_instance_search_or, "--or", "perform an OR query on input filters", tags = tags)

        def __search(self):
            return self.options.get(_instance_search)

        def __search_joiner(self):
            return 'OR' if self.options.get(_instance_search_or, False) else 'AND'


        def __parse_order(self, optional = '--order', help_text = _order_help_text, tags = None):
            if not tags:
                tags = ['list', 'ordering']

            self.parse_variables(_instance_order, optional, str, help_text,
                value_label = '[~]FIELD',
                default = [],
                tags = tags
            )

        def __order(self):
            return self.options.get(_instance_order)

        def __parse_limit(self, optional = '--limit', help_text = _limit_help_text, tags = None):
            if not tags:
                tags = ['list', 'limit']

            self.parse_variable(_instance_limit, optional, int, help_text,
                value_label = 'NUM',
                default = 100,
                tags = tags
            )

        def __limit(self):
            return int(self.options.get(_instance_limit))

        def __instances(self):
            facade = getattr(self, "_{}".format(_facade_name))
            search = getattr(self, _instance_search)
            joiner = getattr(self, _instance_search_joiner)

            self.set_scope(facade)
            return self.search_instances(facade, search, joiner)

        _methods["parse_{}".format(_instance_search)] = __parse_search
        _methods[_instance_search] = property(__search)
        _methods[_instance_search_joiner] = property(__search_joiner)
        _methods["parse_{}".format(_instance_order)] = __parse_order
        _methods[_instance_order] = property(__order)
        _methods["parse_{}".format(_instance_limit)] = __parse_limit
        _methods[_instance_limit] = property(__limit)

        if 'model' in _info:
            _methods["{}_instances".format(_name)] = property(__instances)
