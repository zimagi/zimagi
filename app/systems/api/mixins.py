from utility.runtime import check_api_test

from systems.api.pagination import TestResultSetPagination, ResultNoPagination

import logging


logger = logging.getLogger(__name__)


class FilterViewSetMixin(object):
    action_filters = {}
    filter_backends = ()

    def get_filter_classes(self):
        try:
            filters = self.action_filters[self.action]

            if isinstance(filters, str):
                filters = self.action_filters[filters]

            return filters

        except (KeyError, AttributeError) as e:
            logger.error("Error on filter: {}".format(e))
            return ()

    def filter_queryset(self, queryset):
        self.filter_backends = self.get_filter_classes()
        return super().filter_queryset(queryset)


class PaginationViewSetMixin(object):

    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            elif check_api_test(self.request):
                self._paginator = TestResultSetPagination()
            elif not self._allow_pagination(self.request):
                self._paginator = ResultNoPagination()
            else:
                self._paginator = self.pagination_class()

        return self._paginator


    def _allow_pagination(self, request = None):
        if request and 'page' in request.query_params and int(request.query_params['page']) == 0:
            return False
        return True


class SerializerViewSetMixin(object):
    action_serializers = {}

    def get_serializer_class(self):
        try:
            if check_api_test(self.request):
                if 'test' in self.action_serializers:
                    serializer = self.action_serializers['test']
                else:
                    raise AttributeError()
            else:
                serializer = self.action_serializers[self.action]

            if isinstance(serializer, str):
                serializer = self.action_serializers[serializer]

            return serializer

        except (KeyError, AttributeError):
            return super().get_serializer_class()