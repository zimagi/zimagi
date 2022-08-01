from django.db.models import F

from .base import BaseObject, BaseParser

import logging


logger = logging.getLogger(__name__)


class FieldProcessor(BaseObject):

    def __init__(self, name, provider, field, args = None, options = None):
        self.name     = name
        self.provider = provider
        self.field    = field
        self.args     = args if args else []
        self.options  = options if options else {}


class FieldProcessorParser(BaseParser):
    #
    # Parser indexes
    #
    tokens = [
        *BaseParser.tokens,

        'PROCESSOR_NAME'
    ]

    #
    # Token definitions (in order)
    #
    def t_PROCESSOR_NAME(self, t):
        r'[a-zA-Z0-9]+[a-zA-Z0-9\_\-]+[a-zA-Z0-9]+(?=\()'
        return t

    #
    # Parser evaluation
    #
    def process(self, statement):
        if isinstance(statement, F):
            return statement.name
        return statement

    #
    # Parser rules
    #
    base_parsers = (
        'p_parameters',
    )

    def p_expression_assignment(self, p):
        '''
        expression : NAME EQUALS expression
        '''
        if isinstance(p[3], FieldProcessor):
            p[3].name = p[1]
            p[0] = p[3]
            logger.debug("name = processor: {}".format(p[0]))


    def p_expression_processor(self, p):
        '''
        expression : processor
        '''
        p[0] = p[1]
        logger.debug("processor: {}".format(p[0]))


    def p_processor(self, p):
        '''
        processor : PROCESSOR_NAME LPAR NAME RPAR
        '''
        processor_name = p[1]
        field_name     = p[3]

        p[0] = FieldProcessor(
            name = "{}({})".format(
                processor_name,
                field_name
            ),
            provider = processor_name,
            field    = field_name
        )
        logger.debug("processor: {}".format(p[0]))

    def p_processor_with_args(self, p):
        '''
        processor : PROCESSOR_NAME LPAR NAME SEP parameters RPAR
        '''
        processor_name = p[1]
        field_name     = p[3]
        arguments      = []
        options        = {}

        for parameter in p[5]:
            if parameter[0] == 'ARG':
                arguments.append(parameter[1].name if isinstance(parameter[1], F) else parameter[1])
            else:
                options[parameter[1]] = parameter[2].name if isinstance(parameter[2], F) else parameter[2]

        p[0] = FieldProcessor(
            name = "{}({}{})".format(
                processor_name,
                "{},".format(field_name) if arguments or options else field_name,
                "{},".format(",".join(arguments)) if options else ",".join(arguments),
                ",".join([ "{}={}".format(key, value) for key, value in options.items() ])
            ),
            provider = processor_name,
            field    = field_name,
            args     = arguments,
            options  = options
        )
        logger.debug("processor: {}".format(p[0]))
