
import argparse


class SingleValue(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        values = values[0] if isinstance(values, (list, tuple)) else values
        setattr(namespace, self.dest, values)

class MultiValue(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        if not values:
            values = []
        setattr(namespace, self.dest, values)    

class KeyValues(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        options = {}

        if values: 
            for key_value in values:
                key, value = key_value.split("=")
                options[key] = value
        else:
            options = {}
        
        setattr(namespace, self.dest, options)


def parse_var(parser, name, type, help, optional = False):
    nargs = '?' if optional else 1
    parser.add_argument(
            name,
            action = SingleValue,
            nargs = nargs, 
            type = type, 
            help = help
        )

def parse_vars(parser, name, value_label, type, help, optional = False):
    nargs = '*' if optional else '+'
    parser.add_argument(
            name,
            action = MultiValue,
            nargs = nargs,
            metavar = value_label, 
            type = type, 
            help = help
        )

def parse_key_values(parser, name, value_label, help, optional = False):
    nargs = '*' if optional else '+'
    parser.add_argument(
        name, 
        action = KeyValues, 
        nargs = nargs, 
        metavar = value_label,
        help = help
    )
