from .base import BaseParser

import logging


logger = logging.getLogger(__name__)


class FilterParser(BaseParser):
    #
    # Parser rules
    #
    base_parsers = (
        'p_expression_boolean',
        'p_expression_number',
        'p_expression_string',
        'p_expression_field',
        'p_expression_db_function',
        'p_expression_paren',
        'p_expression_calculation'
    )
