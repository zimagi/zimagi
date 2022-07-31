from django.db.models import F

from .base import BaseParser

import logging


logger = logging.getLogger(__name__)


class OrderParser(BaseParser):
    #
    # Parser indexes
    #
    tokens = [
        *BaseParser.tokens,

        'DASH',
        'TILDE'
    ]

    #
    # Token definitions (in order)
    #
    t_DASH = r'\-'
    t_TILDE = r'\~'

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
        'p_expression_field',
        'p_expression_db_function'
    )

    def p_expression_field_negation(self, p):
        '''
        expression : DASH NAME
                   | TILDE NAME
                   | DASH db_function
                   | TILDE db_function
        '''
        p[0] = "-{}".format(p[2].name if isinstance(p[2], F) else p[2])
        logger.debug("[-|~]field: {}".format(p[0]))
