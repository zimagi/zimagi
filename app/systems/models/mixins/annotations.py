from django.db.models import Count, Avg, Min, Max, Sum, StdDev, Variance
from django.contrib.postgres.aggregates import Corr, CovarPop, RegrAvgX, RegrAvgY, RegrCount, RegrIntercept, RegrR2, RegrSlope, RegrSXX, RegrSXY, RegrSYY

from ..aggregates import Concat
from utility.data import ensure_list

import copy


class ModelFacadeAnnotationMixin(object):

    def __init__(self):
        super().__init__()

        self._annotations = {}


    @property
    def aggregator_map(self):
        return {
            'CONCAT': {
                'class': Concat,
                'types': [],
                'distinct': True
            },
            'COUNT': {
                'class': Count,
                'types': ['bool', 'number', 'text', 'date', 'time'],
                'distinct': True
            },
            'AVG': {
                'class': Avg,
                'types': ['number'],
                'distinct': False
            },
            'MIN': {
                'class': Min,
                'types': ['number'],
                'distinct': False
            },
            'MAX': {
                'class': Max,
                'types': ['number'],
                'distinct': False
            },
            'SUM': {
                'class': Sum,
                'types': ['number'],
                'distinct': False
            },
            'STDDEV': {
                'class': StdDev,
                'types': ['number'],
                'distinct': False
            },
            'VAR': {
                'class': Variance,
                'types': ['number'],
                'distinct': False
            },
            'CORR': {
                'class': Corr,
                'types': [],
                'distinct': False
            },
            'COVAR_POP': {
                'class': CovarPop,
                'types': [],
                'distinct': False
            },
            'REGR_AVG_X': {
                'class': RegrAvgX,
                'types': [],
                'distinct': False
            },
            'REGR_AVG_Y': {
                'class': RegrAvgY,
                'types': [],
                'distinct': False
            },
            'REGR_COUNT': {
                'class': RegrCount,
                'types': [],
                'distinct': False
            },
            'REGR_INTERCEPT': {
                'class': RegrIntercept,
                'types': [],
                'distinct': False
            },
            'REGR_R2': {
                'class': RegrR2,
                'types': [],
                'distinct': False
            },
            'REGR_SLOPE': {
                'class': RegrSlope,
                'types': [],
                'distinct': False
            },
            'REGR_SXX': {
                'class': RegrSXX,
                'types': [],
                'distinct': False
            },
            'REGR_SXY': {
                'class': RegrSXY,
                'types': [],
                'distinct': False
            },
            'REGR_SYY': {
                'class': RegrSYY,
                'types': [],
                'distinct': False
            }
        }

    def get_aggregators(self, type):
        aggregators = []

        for function, info in self.aggregator_map.items():
            if type in info['types']:
                aggregators.append(function)

        return aggregators


    def add_annotations(self, **annotations):
        for field, info in annotations.items():
            if isinstance(info, (list, tuple)):
                # [ FUNCTION, EXPRESSION, ..., OPTIONS ]
                info   = copy.deepcopy(ensure_list(info))
                params = info.pop() if isinstance(info[-1], dict) else {}

                if isinstance(info[0], str) and info[0] in self.aggregator_map:
                    self._annotations[field] = self.aggregator_map[info[0]]['class'](*info[1:], **params)
            else:
                self._annotations[field] = info

        return self

    def set_annotations(self, **annotations):
        self._annotations = {}
        return self.add_annotations(**annotations)

    def get_annotations(self, copy_data = True):
        return copy.deepcopy(self._annotations) if copy_data else self._annotations

    def check_annotations(self):
        return True if self._annotations else False
