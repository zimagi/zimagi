from django.db.models import F

from .base import BaseParser

import logging


logger = logging.getLogger(__name__)


class FunctionParser(BaseParser):
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
        'p_expression_db_function',
    )
