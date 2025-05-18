#!/usr/bin/env python3
import os
import sys

if __name__ == "__main__":
    from systems.client.cli import client

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.client")
    client.execute(sys.argv)
