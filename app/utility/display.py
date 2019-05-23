from contextlib import contextmanager
from terminaltables import AsciiTable

from django.conf import settings

from .runtime import Runtime
from .text import wrap
from .terminal import colorize_data

import os
import sys
import traceback
import re


def format_table(data, prefix = None):
    data = colorize_data(data)
    table_rows = AsciiTable(data).table.splitlines()
    prefixed_rows = []

    if prefix:
        for row in table_rows:
            prefixed_rows.append("{}{}".format(prefix, row))
    else:
        prefixed_rows = table_rows

    return ("\n".join(prefixed_rows), len(table_rows[0]))


def format_list(data, prefix = None, row_labels = False):
    width = Runtime.width()
    data = colorize_data(data)
    prefixed_text = []

    if not row_labels:
        labels = list(data[0])
        values = data[1:]
    else:
        values = data

    def format_item(item):
        text = [
            "=" * width
        ]
        if row_labels:
            text.extend([
                " ** {}".format(item[0]),
                "-" * width
            ])
            for index, value in enumerate(item[1:]):
                text.extend([
                    'value',
                    ''
                ])
        else:
            for index, label in enumerate(labels):
                value = str(item[index]).strip()

                text.extend([
                    " ** {}".format(label),
                    "-" * width,
                    'value',
                    ''
                ])
        return text

    for item in values:
        text = format_item(item)
        if text:
            prefixed_text.extend(text)

    return "\n".join(prefixed_text)


def format_data(data, prefix = None, row_labels = False):
    data = colorize_data(data)
    table_text, width = format_table(data, prefix)
    if width <= Runtime.width():
        return "\n" + table_text
    else:
        return "\n" + format_list(data, prefix, row_labels = row_labels)


def format_exception_info():
    exc_type, exc_value, exc_tb = sys.exc_info()
    return traceback.format_exception(exc_type, exc_value, exc_tb)

def print_exception_info():
    if Runtime.debug():
        sys.stderr.write('\n'.join([ item.strip() for item in format_exception_info() ]) + '\n')

def format_traceback():
    return traceback.format_stack()[:-2]

def print_traceback():
    if Runtime.debug():
        sys.stderr.write('\n'.join([ item.strip() for item in format_traceback() ]) + '\n')


@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout