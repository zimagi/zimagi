from utility import config


class MetaDataMixin(type):
      
    def __new__(cls, name, bases, attr):
        if 'schema' in attr:
            for name, info in attr['schema'].items():
                cls._name_methods(attr, name, info)
                cls._fields_methods(attr, name, info)
                
                if 'model' in info:
                    cls._facade_methods(attr, name, info['model'])
                    cls._search_methods(attr, name, info)
                
                if info.get('provider', False):
                    cls._provider_methods(attr, name, info)

        return super().__new__(cls, name, bases, attr)


    @classmethod
    def _facade_methods(cls, _methods, _name, _model_cls):
        def __facade(self):
            return self.facade(_model_cls.facade)
            
        _methods["_{}".format(_name)] = property(__facade)


    @classmethod
    def _provider_methods(cls, _methods, _name, _info):
        _provider_name = "{}_provider_name".format(_name)
        _provider = "{}_provider".format(_name)
            
        _full_name = _info.get('full_name', _name).lower()
        _default = _info.get('default', 'internal')
        _help_text = 'system {} provider (default @{}|{})'.format(
            _full_name,
            _provider,
            _default
        )

        def __parse_provider_name(self, optional = '--provider', help_text = _help_text):
            self.parse_variable(_provider_name, optional, str, help_text, 
            value_label = 'NAME'
        )

        def __provider_name(self):
            name = self.options.get(_provider_name, None)
            if not name:
                name = self.get_config(_provider, required = False)
            if not name:
                name = config.Config.string(_provider.upper(), _default)
            return name

        def __provider(self):
            return self.get_provider(_name, getattr(self, _provider_name))
            
        _methods["parse_{}".format(_provider_name)] = __parse_provider_name
        _methods[_provider_name] = property(__provider_name)
        _methods[_provider] = property(__provider)


    @classmethod
    def _name_methods(cls, _methods, _name, _info):
        _instance_name = "{}_name".format(_name)
        _instance_names = "{}_names".format(_name)
            
        _plural = _info.get('plural', "{}s".format(_name))
        _full_name = _info.get('full_name', _name).lower()
        _default = _info.get('name_default', None)
            
        _help_text = "{} name".format(_full_name)
        _multi_help_text = "one or more {}s",format(_help_text)
            
        def __parse_name(self, optional = False, help_text = _help_text):
            self.parse_variable(_instance_name, optional, str, help_text, 
                value_label = 'NAME'
            )

        def __name(self):
            name = self.options.get(_instance_name, None)
            if not name:
                name = self.get_config(_instance_name, required = False)
            if not name and _default:
                value = getattr(self, _default, None)
                if value:
                    name = value
                else:
                    name = _default
            return name
                
        def __parse_names(self, optional = "--{}".format(_plural), help_text = _multi_help_text):
            self.parse_variables(_instance_names, optional, str, help_text, 
                value_label = 'NAME'
            )

        def __names(self):
            return self.options.get(_instance_names, [])

        def __accessor(self):
            return self.get_instance(
                getattr(self, "_{}".format(_name)), 
                getattr(self, _instance_name)
            )

        _methods["parse_{}".format(_instance_name)] = __parse_name
        _methods[_instance_name] = property(__name)
        _methods["parse_{}".format(_instance_names)] = __parse_names
        _methods[_instance_names] = property(__names)

        if 'model' in _info:
            _methods[_name] = property(__accessor)


    @classmethod
    def _fields_methods(cls, _methods, _name, _info):
        _instance_fields = "{}_fields".format(_name)
        
        _system_fields = _info.get('system_fields', [])
        _full_name = _info.get('full_name', _name).lower()
        _help_text = "{} fields".format(_full_name)
            
        def __parse_fields(self, optional = True, help_callback = None):
            facade = getattr(self, "_{}".format(_name)) if 'model' in _info else None
            self.parse_fields(facade, _instance_fields, 
                optional = optional, 
                excluded_fields = _system_fields,
                help_callback = help_callback,
                callback_args = [_name]
            )

        def __fields(self):
            return self.options.get(_instance_fields, {})
            
        _methods["parse_{}".format(_instance_fields)] = __parse_fields
        _methods[_instance_fields] = property(__fields)
    

    @classmethod
    def _search_methods(cls, _methods, _name, _info):
        _instance_search = "{}_search".format(_name)
        _instance_order = "{}_order".format(_name)

        _full_name = _info.get('full_name', _name).lower()
        _search_help_text = "{} search filters".format(_full_name)
        _order_help_text = "{} ordering fields (~field for desc)".format(_full_name)
            
        def __parse_search(self, optional = True, help_text = _search_help_text):
            self.parse_variables(_instance_search, optional, str, help_text, 
                value_label = 'REFERENCE'
            )

        def __search(self):
            return self.options.get(_instance_search, [])

        def __parse_order(self, optional = '--order', help_text = _order_help_text):
            self.parse_variables(_instance_order, optional, str, help_text, 
                value_label = '[~]FIELD'
            )

        def __order(self):
            return self.options.get(_instance_order, [])

        def __instances(self):
            return self.search_instances(
                getattr(self, "_{}".format(_name)), 
                getattr(self, _instance_search)
            )
            
        _methods["parse_{}".format(_instance_search)] = __parse_search
        _methods[_instance_search] = property(__search)
        _methods["parse_{}".format(_instance_order)] = __parse_order
        _methods[_instance_order] = property(__order)

        if 'model' in _info:
            _methods["{}_instances".format(_name)] = property(__instances)
