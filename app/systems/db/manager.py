import logging
import os
from collections import OrderedDict
from io import StringIO

from django.apps import apps
from django.conf import settings
from django.core import serializers
from django.core.management.color import no_style
from django.db import DEFAULT_DB_ALIAS, connections, router, transaction
from utility.data import ensure_list
from utility.filesystem import load_file, save_file

logger = logging.getLogger(__name__)


def get_apps():
    return OrderedDict.fromkeys(app_config for app_config in apps.get_app_configs() if app_config.models_module is not None)


def get_objects(alias, packages):
    packages = ensure_list(packages)

    for model in serializers.sort_dependencies(get_apps().items()):
        if getattr(model, "facade", None):
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
        objects = serializers.deserialize(
            "json", str_conn, using=alias, ignorenonexistent=True, handle_forward_references=True
        )
        for obj in objects:
            if router.allow_migrate_model(alias, obj.object.__class__):
                models.add(obj.object.__class__)
                obj.save(using=alias)
    finally:
        str_conn.close()

    return models


class DatabaseManager:
    def __init__(self, alias=DEFAULT_DB_ALIAS):
        self.alias = alias
        self.connection = connections[self.alias]

    def _load(self, str_data):
        logger.debug("Loaded: %s", str_data)
        try:
            logger.debug("Importing: %s", str_data)

            with transaction.atomic(using=self.alias):
                with self.connection.constraint_checks_disabled():
                    models = parse_objects(self.alias, str_data)

                table_names = [model._meta.db_table for model in models]
                self.connection.check_constraints(table_names=table_names)

                sequence_sql = self.connection.ops.sequence_reset_sql(no_style(), models)
                if sequence_sql:
                    with self.connection.cursor() as cursor:
                        for line in sequence_sql:
                            cursor.execute(line)

        except Exception as e:
            e.args = (f"Problem installing data: {e}",)
            logger.exception("Exception: %s", e)
            raise e

    def load(self, str_data):
        self._load(str_data)

    def load_file(self, file_path):
        if os.path.isfile(file_path):
            self._load(load_file(file_path))

    def _save(self, packages):
        str_conn = StringIO()
        try:
            serializers.serialize(
                "json",
                get_objects(self.alias, packages),
                indent=2,
                use_natural_foreign_keys=False,
                use_natural_primary_keys=False,
                stream=str_conn,
            )
            str_data = str_conn.getvalue()
            logger.debug("Updated: %s", str_data)

        except Exception as e:
            e.args = (f"Problem saving data: {e}",)
            logger.exception("Exception: %s", e)
            raise

        finally:
            str_conn.close()

        return str_data

    def save(self, packages=settings.DB_PACKAGE_ALL_NAME):
        return self._save(packages)

    def save_file(self, file_path, packages=settings.DB_PACKAGE_ALL_NAME):
        str_data = self._save(packages)
        if str_data:
            save_file(file_path, str_data)
