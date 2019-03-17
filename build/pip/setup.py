import setuptools
import os
import importlib.util


setup_path = os.path.dirname(os.path.realpath(__file__))
asset_path = os.path.join(setup_path, '..', 'assets')
base_path = os.path.join(setup_path, '..', '..')
app_path = os.path.join(base_path, 'app')


spec = importlib.util.spec_from_file_location('version', os.path.join(app_path, 'settings', 'version.py'))
version = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version)

with open(os.path.join(base_path, 'README.md'), 'r') as file:
    long_description = file.read()


setuptools.setup(
    name = "cenv",
    version = version.VERSION,
    author = "Adrian Webb",
    author_email = "adrian@webb.sh",
    description = "Modular Command Execution Environment",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/venturiscm/cenv",
    license = 'Apache 2.0',
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    scripts = [
        os.path.join(asset_path, 'ce')
    ]
)
