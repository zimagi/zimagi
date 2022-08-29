from types import MethodType

from django.db.models import F

from ..errors import ParseError
from utility.data import dump_json

import sys
import operator
import ply.lex as lex
import ply.yacc as yacc
import logging


logger = logging.getLogger(__name__)


class PlyLogger(object):

    def __init__(self, handle):
        self.handle = handle

    def debug(self, msg, *args, **kwargs):
        self.handle.write((msg % args) + '\n')

    info = debug

    def warning(self, msg, *args, **kwargs):
        if msg not in (
            'Token %r defined, but not used',
            'There are %d unused tokens'
        ):
            self.handle.write('WARNING: ' + (msg % args) + '\n')

    def error(self, msg, *args, **kwargs):
        self.handle.write('ERROR: ' + (msg % args) + '\n')

    critical = debug


class BaseObject(object):

    def __str__(self):
        return dump_json(self.__dict__, indent = 2)

    def __repr__(self):
        return self.__str__()


class BaseParser(object):
    #
    # Parser indexes
    #
    tokens = [
        'NAME',
        'DB_FUNCTION_NAME',

        'BOOL',
        'INT',
        'FLOAT',
        'QUOTED_STRING',
        'DOUBLE_QUOTED_STRING',

        'ADD',
        'SUBTRACT',
        'MULTIPLY',
        'DIVIDE',
        'MODULO',
        'POWER',

        'LPAR',
        'RPAR',
        'EQUALS',
        'SEP',
        'KSEP',

        'LBR',
        'RBR',

        'LCBR',
        'RCBR'
    ]

    precedence = (
        ('left', 'ADD', 'SUBTRACT'),
        ('left', 'MULTIPLY', 'DIVIDE', 'MODULO'),
        ('left', 'POWER'),
        ('left', 'LPAR', 'RPAR')
    )

    parser_index = {
        'p_expression_boolean': (),
        'p_expression_number': (),
        'p_expression_string': (),
        'p_expression_field': (),

        'p_expression_list': (
            'p_empty_list',
            'p_list'
        ),
        'p_expression_dictionary': (
            'p_empty_dictionary',
            'p_dictionary'
        ),

        'p_expression_db_function': (
            'p_db_function',
            'p_db_function_with_params'
        ),

        'p_expression_paren': (),
        'p_expression_calculation': (),

        'p_empty_list': (),
        'p_list': (
            'p_list_elements',
            'p_list_elements_single'
        ),
        'p_list_elements': (
            'p_list_element',
        ),
        'p_list_elements_single': (
            'p_list_element',
        ),
        'p_list_element': (),

        'p_empty_dictionary': (),
        'p_dictionary': (
            'p_dictionary_elements',
            'p_dictionary_elements_single'
        ),
        'p_dictionary_elements': (
            'p_dictionary_element',
        ),
        'p_dictionary_elements_single': (
            'p_dictionary_element',
        ),
        'p_dictionary_element': (),

        'p_db_function': (),
        'p_db_function_with_params': (
            'p_parameters',
            'p_parameters_single'
        ),

        'p_parameters': (
            'p_parameter_argument_data',
            'p_parameter_argument_field',
            'p_parameter_option'
        ),
        'p_parameters_single': (
            'p_parameter_argument_data',
            'p_parameter_argument_field',
            'p_parameter_option'
        ),

        'p_parameter_argument_data': (
            'p_empty_list',
            'p_list',
            'p_empty_dictionary',
            'p_dictionary'
        ),
        'p_parameter_argument_field': (
            'p_db_function',
            'p_db_function_with_params'
        ),
        'p_parameter_option': (
            'p_empty_list',
            'p_list',
            'p_empty_dictionary',
            'p_dictionary'
        )
    }

    operations = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
        '%': operator.mod,
        '^': operator.pow
    }

    #
    # Parser initialization
    #
    def __init__(self, facade = None):
        self.facade = facade

        self.generate()

        self.lexer   = lex.lex(
            module   = self,
            optimize = False,
            debug    = False,
            errorlog = PlyLogger(sys.stderr)
        )
        self.parser = yacc.yacc(
            module       = self,
            start        = 'statement',
            optimize     = False,
            debug        = False,
            write_tables = False,
            errorlog     = PlyLogger(sys.stderr)
        )

    #
    # Parser evaluation
    #
    def generate(self):
        def attach_parser(parser):
            if getattr(self, parser, None) is None:
                setattr(self, parser, MethodType(getattr(sys.modules[__name__], parser), self))

                for dependency in self.parser_index[parser]:
                    attach_parser(dependency)

        for parser in self.base_parsers:
            attach_parser(parser)


    def evaluate(self, value):
        logger.info("===== Query filter statement ===== ( {} )".format(value))
        logger.info("  === Active base parsers === {}".format(self.base_parsers))
        return self.parser.parse(value)

    def process(self, statement):
        # Override in subclass if needed
        return statement

    #
    # Parser errors
    #
    def t_error(self, t):
        raise ParseError("Illegal expression in query parser: {}".format(t.value))

    def p_error(self, p):
        raise ParseError("Parse error: {}".format(p))


    #
    # Token definitions (in order)
    #
    def t_BOOL(self, t):
        r'(TRUE|True|true|FALSE|False|false)'
        if t.value.lower() == 'true':
            t.value = True
        else:
            t.value = False
        return t

    def t_FLOAT(self, t):
        r'\-?\d*\.\d+'
        t.value = float(t.value)
        return t

    def t_INT(self, t):
        r'\-?\d+'
        t.value = int(t.value)
        return t

    def t_DB_FUNCTION_NAME(self, t):
        r'[a-zA-Z0-9]+[a-zA-Z0-9\_\-]+[a-zA-Z0-9]+\:[A-Z0-9\_]+'
        t.value = tuple(t.value.split(':'))
        return t

    def t_NAME(self, t):
        r'[a-zA-Z0-9]+[a-zA-Z0-9\_\-]*[a-zA-Z0-9]+'
        return t

    def t_QUOTED_STRING(self, t):
        r'\'[^\'\\]*(?:\\[\S\s][^\'\\]*)*\''
        t.value = t.value[1:-1]
        return t

    def t_DOUBLE_QUOTED_STRING(self, t):
        r'\"[^\"\\]*(?:\\[\S\s][^\"\\]*)*\"'
        t.value = t.value[1:-1]
        return t

    t_EQUALS = r'\='
    t_SEP = r'\,'
    t_KSEP = r'\:'

    t_LPAR = r'\('
    t_RPAR = r'\)'
    t_LBR = r'\['
    t_RBR = r'\]'
    t_LCBR = r'\{'
    t_RCBR = r'\}'

    t_ADD = r'\+'
    t_SUBTRACT = r'\-'
    t_MULTIPLY = r'\*'
    t_DIVIDE = r'\/'
    t_POWER = r'\^'
    t_MODULO = r'\%'

    t_ignore = ' \t'

    #
    # Parser rules
    #
    base_parsers = ()


    def p_statement(self, p):
        '''
        statement : expression
        '''
        logger.info("=== AST         : {}".format(p[1]))
        p[0] = self.process(p[1])
        logger.info("=== Result      : {}".format(p[0]))

        if self.facade:
            logger.info("=== Annotations : {}".format(self.facade.get_annotations(False)))

#
# Optional parser rules (see cls.parsers variable)
#
def p_expression_boolean(self, p):
    '''
    expression : BOOL
    '''
    p[0] = p[1]
    logger.debug("boolean: {}".format(p[0]))

def p_expression_number(self, p):
    '''
    expression : FLOAT
               | INT
    '''
    p[0] = p[1]
    logger.debug("number: {}".format(p[0]))

def p_expression_string(self, p):
    '''
    expression : QUOTED_STRING
               | DOUBLE_QUOTED_STRING
    '''
    p[0] = p[1]
    logger.debug("string: {}".format(p[0]))

def p_expression_list(self, p):
    '''
    expression : list
    '''
    p[0] = p[1]
    logger.debug("list: {}".format(p[0]))

def p_expression_dictionary(self, p):
    '''
    expression : dictionary
    '''
    p[0] = p[1]
    logger.debug("dictionary: {}".format(p[0]))


def p_expression_field(self, p):
    '''
    expression : NAME
    '''
    p[0] = F(p[1])
    logger.debug("identifier: {}".format(p[0]))

def p_expression_db_function(self, p):
    '''
    expression : db_function
    '''
    p[0] = p[1]
    logger.debug("db_function: {}".format(p[0]))

def p_expression_paren(self, p):
    '''
    expression : LPAR expression RPAR
    '''
    p[0] = p[2]
    logger.debug("( expression ): {}".format(p[0]))

def p_expression_calculation(self, p):
    '''
    expression : expression POWER expression
               | expression MODULO expression
               | expression MULTIPLY expression
               | expression DIVIDE expression
               | expression ADD expression
               | expression SUBTRACT expression
    '''
    p[0] = self.operations[p[2]](p[1], p[3])
    logger.debug("expression op expression: {}".format(p[0]))


def p_empty_list(self, p):
    '''
    list : LBR RBR
    '''
    p[0] = []
    logger.debug("empty list: {}".format(p[0]))

def p_list(self, p):
    '''
    list : LBR list_elements RBR
    '''
    p[0] = p[2]
    logger.debug("list: {}".format(p[0]))

def p_list_elements(self, p):
    '''
    list_elements : list_elements SEP list_element
    '''
    p[0] = p[1] + (p[3],)
    logger.debug("list_elements: {}".format(p[0]))

def p_list_elements_single(self, p):
    '''
    list_elements : list_element
    '''
    p[0] = (p[1],)
    logger.debug("list_elements: {}".format(p[0]))

def p_list_element(self, p):
    '''
    list_element : BOOL
                 | INT
                 | FLOAT
                 | QUOTED_STRING
                 | DOUBLE_QUOTED_STRING
                 | list
                 | dictionary
    '''
    p[0] = p[1]
    logger.debug("list element: {}".format(p[0]))


def p_empty_dictionary(self, p):
    '''
    dictionary : LCBR RCBR
    '''
    p[0] = {}
    logger.debug("empty dictionary: {}".format(p[0]))

def p_dictionary(self, p):
    '''
    dictionary : LCBR dictionary_elements RCBR
    '''
    dictionary = {}
    for element in p[2]:
        dictionary[element[0]] = element[1]

    p[0] = dictionary
    logger.debug("dictionary: {}".format(p[0]))

def p_dictionary_elements(self, p):
    '''
    dictionary_elements : dictionary_elements SEP dictionary_element
    '''
    p[0] = p[1] + (p[3],)
    logger.debug("dictionary_elements: {}".format(p[0]))

def p_dictionary_elements_single(self, p):
    '''
    dictionary_elements : dictionary_element
    '''
    p[0] = (p[1],)
    logger.debug("dictionary_elements: {}".format(p[0]))

def p_dictionary_element(self, p):
    '''
    dictionary_element : QUOTED_STRING KSEP BOOL
                       | QUOTED_STRING KSEP INT
                       | QUOTED_STRING KSEP FLOAT
                       | QUOTED_STRING KSEP QUOTED_STRING
                       | QUOTED_STRING KSEP DOUBLE_QUOTED_STRING
                       | QUOTED_STRING KSEP list
                       | QUOTED_STRING KSEP dictionary
                       | DOUBLE_QUOTED_STRING KSEP BOOL
                       | DOUBLE_QUOTED_STRING KSEP INT
                       | DOUBLE_QUOTED_STRING KSEP FLOAT
                       | DOUBLE_QUOTED_STRING KSEP QUOTED_STRING
                       | DOUBLE_QUOTED_STRING KSEP DOUBLE_QUOTED_STRING
                       | DOUBLE_QUOTED_STRING KSEP list
                       | DOUBLE_QUOTED_STRING KSEP dictionary
    '''
    p[0] = (p[1], p[3])
    logger.debug("dictionary element: {}".format(p[0]))


def p_db_function(self, p):
    '''
    db_function : DB_FUNCTION_NAME
                | DB_FUNCTION_NAME LPAR RPAR
    '''
    field_name  = ":".join(p[1])
    function    = p[1][1]
    annotations = {
        field_name: [ function, F(p[1][0]) ]
    }
    if self.facade:
        self.facade.add_annotations(**annotations)

    p[0] = F(field_name)
    logger.debug("db_function: {} {}".format(p[0], annotations))

def p_db_function_with_params(self, p):
    '''
    db_function : DB_FUNCTION_NAME LPAR parameters RPAR
    '''
    field_name = ":".join(p[1])
    function   = p[1][1]
    arguments  = [ F(p[1][0]) ]
    options    = {}

    for parameter in p[3]:
        if parameter[0] == 'ARG':
            arguments.append(parameter[1])
        else:
            options[parameter[1]] = parameter[2]

    annotations = {
        field_name: [ function, *arguments, options ]
    }

    if self.facade:
        self.facade.add_annotations(**annotations)

    p[0] = F(field_name)
    logger.debug("db_function: {} {}".format(p[0], annotations))


def p_parameters(self, p):
    '''
    parameters : parameters SEP parameter
    '''
    if isinstance(p[1][0], tuple):
        parameters = [ parameter for parameter in p[1] ]
    else:
        parameters = [ p[1] ]

    parameters.append(p[3])
    p[0] = tuple(parameters)
    logger.debug("parameters: {}".format(p[0]))

def p_parameters_single(self, p):
    '''
    parameters : parameter
    '''
    p[0] = (p[1],)
    logger.debug("parameters: {}".format(p[0]))


def p_parameter_argument_data(self, p):
    '''
    parameter : BOOL
              | INT
              | FLOAT
              | QUOTED_STRING
              | DOUBLE_QUOTED_STRING
              | list
              | dictionary
    '''
    p[0] = ('ARG', p[1])
    logger.debug("data argument: {}".format(p[0]))

def p_parameter_argument_field(self, p):
    '''
    parameter : NAME
              | db_function
    '''
    p[0] = ('ARG', F(p[1]))
    logger.debug("field argument: {}".format(p[0]))

def p_parameter_option(self, p):
    '''
    parameter : NAME EQUALS BOOL
              | NAME EQUALS INT
              | NAME EQUALS FLOAT
              | NAME EQUALS QUOTED_STRING
              | NAME EQUALS DOUBLE_QUOTED_STRING
              | NAME EQUALS list
              | NAME EQUALS dictionary
    '''
    p[0] = ('OPTION', p[1], p[3])
    logger.debug("option: {}".format(p[0]))
