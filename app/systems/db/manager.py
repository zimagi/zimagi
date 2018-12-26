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

                try:
                    obj.save(using = alias)
                    
                except (DatabaseError, IntegrityError, ValueError) as e:
                    e.args = ("Could not load %(app_label)s.%(object_name)s(pk=%(pk)s): %(error_msg)s" % {
                        'app_label': obj.object._meta.app_label,
                        'object_name': obj.object._meta.object_name,
                        'pk': obj.object.pk,
                        'error_msg': e
                    })
                    raise
    finally:
        str_conn.close() 
       
    return models


class DatabaseManager(object):

    def __init__(self, alias = DEFAULT_DB_ALIAS):
        self.alias = alias
        self.connection = connections[self.alias]
    

    def load(self, str_data, encrypted = True):
        try:
            if encrypted:
                str_data = Cipher.get().decrypt(str_data)
        
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
            
            if transaction.get_autocommit(self.alias):
                self.connection.close()
        
        except Exception as e:
            e.args = ("Problem installing data: {}".format(e),)
            raise


    def load_file(self, file_path = None, encrypted = True):
        if not file_path:
            file_path = settings.DATA_PATH
            encrypted = settings.DATA_ENCRYPT

        if os.path.isfile(file_path):
            with open(file_path, 'rb') as file:
                self.load(file.read(), encrypted)


    def save(self, package, encrypted = True):
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
                
            if encrypted:
                str_data = Cipher.get().encrypt(str_data)
        
        except Exception as e:
            e.args = ("Problem saving data: {}".format(e),)
            raise

        finally:
            str_conn.close()

        return str_data

    def save_file(self, package, file_path = None, encrypted = True):
        if not file_path:
            file_path = settings.DATA_PATH
            encrypted = settings.DATA_ENCRYPT

        with open(file_path, 'wb') as file:
            str_data = self.save(package, encrypted)
            file.write(str_data)
