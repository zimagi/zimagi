from .base import BaseParser
from .field_processors import FieldProcessor, FieldProcessorParser

import logging


logger = logging.getLogger(__name__)


class FieldParser(
    FieldProcessorParser,
    BaseParser
):
    base_parsers = (
        'p_expression_number',
        'p_expression_field',
        'p_expression_db_function',
        'p_expression_paren',
        'p_expression_calculation'
    )

    def p_expression_assignment(self, p):
        '''
        expression : NAME EQUALS expression
        '''
        if isinstance(p[3], FieldProcessor):
            p[3].name = p[1]
            p[0] = p[3]
            logger.debug("name = processor: {}".format(p[0]))
        else:
            annotations = { p[1]: p[3] }

            if self.facade:
                self.facade.add_annotations(**annotations)

            p[0] = p[1]
            logger.debug("name = value: {} {}".format(p[0], annotations))
