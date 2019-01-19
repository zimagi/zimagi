from collections import OrderedDict
from io import StringIO

from django.conf import settings
from django.core import serializers
from django.db import DEFAULT_DB_ALIAS, DatabaseError, IntegrityError, router, connections, transaction
from django.core.management.base import CommandError
from django.core.management.color import no_style
from django.apps import apps

from utility.encryption import Cipher

import os
import json
import logging


logger = logging.getLogger(__name__)


PACKAGE_ALL_NAME = 'all'


def get_apps():
    return OrderedDict.fromkeys(
        app_config for app_config in apps.get_app_configs()
        if app_config.models_module is not None
    )


def get_objects(alias, package):
    for model in serializers.sort_dependencies(get_apps().items()):
        if not getattr(model, 'facade', None) or package not in model.facade.get_packages():
            continue
             
        if router.allow_migrate_model(alias, model):
            queryset = model._base_manager.using(alias).order_by(model._meta.pk.name)
            yield from queryset.iterator()


def parse_objects(alias, json_data):
    str_conn = StringIO(json_data)
    str_conn.seek(0)

    models = set()    
    try:
        objects = serializers.deserialize('json', str_conn, 
            using = alias, 
            ignorenonexistent = True,
            handle_forward_references = True
        )
        for obj in objects:
            if router.allow_migrate_model(alias, obj.object.__class__):
                models.add(obj.object.__class__)
                obj.save(using = alias)
    finally:
        str_conn.close() 
       
    return models


class DatabaseState(object):
    state = {}
    removals = {}

    @classmethod
    def check(cls, alias):
        try:
            return cls.state[alias]
        except Exception:
            return False

    @classmethod
    def set_state(cls, alias, state):
        cls.state[alias] = state


    @classmethod
    def remove(cls, alias):
        try:
            return cls.removals[alias]
        except Exception:
            return False

    @classmethod
    def mark_remove(cls, alias = DEFAULT_DB_ALIAS):
        cls.removals[alias] = True


class DatabaseManager(object):

    def __init__(self, alias = DEFAULT_DB_ALIAS):
        self.alias = alias
        self.connection = connections[self.alias]
    

    def _load(self, str_data, encrypted = True):
        logger.debug("Loaded: %s", str_data)
        try:
            if encrypted:
                str_data = Cipher.get().decrypt(str_data)

            logger.debug("Importing: %s", str_data)
        
            with transaction.atomic(using = self.alias):
                with self.connection.constraint_checks_disabled():
                    models = parse_objects(self.alias, str_data)
            
                table_names = [model._meta.db_table for model in models]
                self.connection.check_constraints(table_names = table_names)

                sequence_sql = self.connection.ops.sequence_reset_sql(no_style(), models)
                if sequence_sql:
                    with self.connection.cursor() as cursor:
                        for line in sequence_sql:
                            cursor.execute(line)
        
        except Exception as e:
            e.args = ("Problem installing data: {}".format(e),)
            logger.exception("Exception: %s", e)
            raise

    def load(self, str_data, encrypted = True):
        self._load(str_data, encrypted)
        DatabaseState.set_state(self.alias, True)

    def load_file(self, file_path = None, encrypted = True):
        from utility.runtime import Runtime
        curr_env = Runtime.get_env()

        if not file_path:
            file_path = self.get_env_path(curr_env)
            encrypted = settings.DATA_ENCRYPT

        if os.path.isfile(file_path):
            with open(file_path, 'rb') as file:
                self._load(file.read(), encrypted)

        DatabaseState.set_state(self.alias, curr_env)


    def _save(self, package, encrypted = True):
        str_conn = StringIO()

        try:        
            serializers.serialize('json', 
                get_objects(self.alias, package), 
                indent = 2,
                use_natural_foreign_keys = True,
                use_natural_primary_keys = True,
                stream = str_conn
            )
            str_data = str_conn.getvalue()

            logger.debug("Updated: %s", str_data)
                
            if encrypted:
                str_data = Cipher.get().encrypt(str_data)
        
        except Exception as e:
            e.args = ("Problem saving data: {}".format(e),)
            logger.exception("Exception: %s", e)
            raise

        finally:
            str_conn.close()

        return str_data

    def save(self, package = PACKAGE_ALL_NAME, encrypted = True):
        str_data = None

        if DatabaseState.check(self.alias):
            str_data = self._save(package, encrypted)
        
        return str_data

    def save_file(self, package = PACKAGE_ALL_NAME, file_path = None, encrypted = True):
        curr_env = DatabaseState.check(self.alias)

        if curr_env:
            if not file_path:
                file_path = self.get_env_path(curr_env)
                encrypted = settings.DATA_ENCRYPT

            if DatabaseState.remove(self.alias):
                os.remove(file_path)
            else:
                with open(file_path, 'wb') as file:
                    str_data = self._save(package, encrypted)
                    logger.debug("Writing: %s", str_data)
                    file.write(str_data)


    def get_env_path(self, env_name):
        return "{}.{}.data".format(settings.BASE_DATA_PATH, env_name)