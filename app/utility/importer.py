from django.conf import settings

import glob
import importlib
import os
import sys
import re


def import_modules(module_dir, base_dir = settings.APP_DIR):
    base_name = re.sub(base_dir + '/', '', module_dir).replace('/', '.')
    package = importlib.import_module(base_name)
    modules = glob.glob(module_dir + "/*.py")
    modules = [ os.path.basename(f)[:-3] for f in modules if os.path.isfile(f) and not f.endswith('__init__.py')]

    for module_name in modules:
        module = importlib.import_module("{}.{}".format(base_name, module_name))
        attributes = module.__dict__
        try:
            import_modules = module.__all__
        except AttributeError:
            import_modules = [ name for name in attributes if not name.startswith('_') ]

        for name in import_modules:
            setattr(package, name, attributes[name])

    importlib.invalidate_caches()

def import_modules_by_init(init_file):
    return import_modules(os.path.dirname(init_file))

