#!/usr/bin/env python3
import os
import sys

if __name__ == "__main__":
    from systems.commands import cli
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.cli")
    cli.execute(sys.argv)
