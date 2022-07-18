from django.db.models import F

from .base import BaseParser

import logging


logger = logging.getLogger(__name__)


class FieldParser(BaseParser):
    #
    # Parser rules
    #
    base_parsers = (
        'p_expression_number',
        'p_expression_field',
        'p_expression_function',
        'p_expression_paren',
        'p_expression_calculation'
    )

    def p_expression_assignment(self, p):
        '''
        expression : NAME EQUALS expression
        '''
        annotations = { p[1].name: p[3] }

        self.facade.add_annotations(**annotations)
        p[0] = p[1]
        logger.debug("name = value: {} {}".format(p[0], annotations))
