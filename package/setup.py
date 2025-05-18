import os
import re

import setuptools

package_path = os.path.dirname(os.path.realpath(__file__))


with open(os.path.join(package_path, "VERSION")) as file:
    version = file.read()

with open(os.path.join(package_path, "README.md")) as file:
    long_description = file.read()

with open(os.path.join(package_path, "requirements.txt")) as file:
    requirements = re.split(r"\n+", file.read())


setuptools.setup(
    name="zimagi",
    version=version,
    author="Adrian Webb",
    author_email="adrian.webb@dccs.tech",
    description="Zimagi CLI and API Client",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zimagi/zimagi",
    license="Apache 2.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=requirements,
    package_dir={"": package_path},
    packages=setuptools.find_packages(where=package_path),
    scripts=[os.path.join(package_path, "bin", "zimagi")],
)
