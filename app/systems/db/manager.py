from collections import OrderedDict
from io import StringIO

from django.conf import settings
from django.core import serializers
from django.db import DEFAULT_DB_ALIAS, router, connections, transaction
from django.core.management.color import no_style
from django.apps import apps

from utility.data import ensure_list
from utility.encryption import Cipher

import os
import logging


logger = logging.getLogger(__name__)


def get_apps():
    return OrderedDict.fromkeys(
        app_config for app_config in apps.get_app_configs()
        if app_config.models_module is not None
    )


def get_objects(alias, packages):
    packages = ensure_list(packages)

    for model in serializers.sort_dependencies(get_apps().items()):
        if getattr(model, 'facade', None):
            facade_packages = model.facade.get_packages()
            if not list(set(packages) & set(facade_packages)):
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


class DatabaseManager(object):

    def __init__(self, alias = DEFAULT_DB_ALIAS):
        self.alias = alias
        self.connection = connections[self.alias]


    def _load(self, str_data, encrypted = True):
        logger.debug("Loaded: %s", str_data)
        try:
            if encrypted:
                str_data = Cipher.get('db').decrypt(str_data)

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
            raise e

    def load(self, str_data, encrypted = True):
        self._load(str_data, encrypted)

    def load_file(self, file_path, encrypted = True):
        if os.path.isfile(file_path):
            file_type = 'rb' if encrypted else 'r'
            with open(file_path, file_type) as file:
                self._load(file.read(), encrypted)


    def _save(self, packages, encrypted = True):
        str_conn = StringIO()
        try:
            serializers.serialize('json',
                get_objects(self.alias, packages),
                indent = 2,
                use_natural_foreign_keys = False,
                use_natural_primary_keys = False,
                stream = str_conn
            )
            str_data = str_conn.getvalue()
            logger.debug("Updated: %s", str_data)

            if encrypted:
                str_data = Cipher.get('db').encrypt(str_data)

        except Exception as e:
            e.args = ("Problem saving data: {}".format(e),)
            logger.exception("Exception: %s", e)
            raise

        finally:
            str_conn.close()

        return str_data

    def save(self, packages = settings.DB_PACKAGE_ALL_NAME, encrypted = True):
        return self._save(packages, encrypted)

    def save_file(self, file_path, packages = settings.DB_PACKAGE_ALL_NAME, encrypted = True):
        str_data = self._save(packages, encrypted)
        if str_data:
            file_type = 'wb' if encrypted else 'w'
            with open(file_path, file_type) as file:
                logger.debug("Writing: %s", str_data)
                file.write(str_data)
