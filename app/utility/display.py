from contextlib import contextmanager
from terminaltables import AsciiTable

from django.conf import settings

import os
import sys
import traceback


def format_table(data, prefix = None):
    table_rows = AsciiTable(data).table.splitlines()
    prefixed_rows = []

    if prefix:
        for row in table_rows:
            prefixed_rows.append("{}{}".format(prefix, row))
    else:
        prefixed_rows = table_rows
    
    return "\n".join(prefixed_rows)

def print_table(data, prefix = None):
    print("\n" + format_table(data, prefix))


def format_exception_info():
    exc_type, exc_value, exc_tb = sys.exc_info()
    return traceback.format_exception(exc_type, exc_value, exc_tb)

def print_exception_info():
    if settings.DEBUG:
        print("\n".join([ item.strip() for item in format_exception_info() ]))

def format_traceback():
    return traceback.format_stack()[:-2]

def print_traceback():
    if settings.DEBUG:
        print("\n".join([ item.strip() for item in format_traceback() ]))


@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout