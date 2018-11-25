
import argparse


class SingleValue(argparse.Action):
     def __call__(self, parser, namespace, values, option_string=None):
         setattr(namespace, self.dest, values[0])


class KeyValues(argparse.Action):
     def __call__(self, parser, namespace, values, option_string=None):
         options = {}
         
         for key_value in values:
             key, value = key_value.split("=")
             options[key] = value
        
         setattr(namespace, self.dest, options)


def parse_var(parser, name, type, help):
    parser.add_argument(
            name,
            action = SingleValue,
            nargs = 1, 
            type = type, 
            help = help
        )

def parse_key_values(parser, name, value_label, help):
    parser.add_argument(
        name, 
        action = KeyValues, 
        nargs = '+', 
        metavar = value_label,
        help = help
    )
