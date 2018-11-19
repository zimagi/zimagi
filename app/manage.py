#!/usr/bin/env python3
import os
import sys

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    
    args = sys.argv
    app_name = args.pop(1)
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.{}.settings".format(app_name))
    execute_from_command_line(args)