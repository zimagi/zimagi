import logging

from django.db.models import F

from .base import BaseObject, BaseParser

logger = logging.getLogger(__name__)


class DataProcessor(BaseObject):
    def __init__(self, provider, args=None, options=None):
        self.provider = provider
        self.args = args if args else []
        self.options = options if options else {}


class DataProcessorParser(BaseParser):
    #
    # Parser indexes
    #
    tokens = [*BaseParser.tokens, "PROCESSOR_NAME"]

    #
    # Token definitions (in order)
    #
    def t_PROCESSOR_NAME(self, t):
        r"[a-zA-Z0-9]+[a-zA-Z0-9\_\-]+[a-zA-Z0-9]+(?=(\(|$))"
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
    base_parsers = ("p_parameters",)

    def p_expression_processor(self, p):
        """
        expression : processor
        """
        p[0] = p[1]
        logger.debug(f"processor: {p[0]}")

    def p_processor(self, p):
        """
        processor : PROCESSOR_NAME
                  | PROCESSOR_NAME LPAR RPAR
        """
        p[0] = DataProcessor(provider=p[1])
        logger.debug(f"processor: {p[0]}")

    def p_processor_with_args(self, p):
        """
        processor : PROCESSOR_NAME LPAR parameters RPAR
        """
        arguments = []
        options = {}

        for parameter in p[3]:
            if parameter[0] == "ARG":
                arguments.append(parameter[1].name if isinstance(parameter[1], F) else parameter[1])
            else:
                options[parameter[1]] = parameter[2].name if isinstance(parameter[2], F) else parameter[2]

        p[0] = DataProcessor(provider=p[1], args=arguments, options=options)
        logger.debug(f"processor: {p[0]}")
