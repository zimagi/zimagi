from collections import OrderedDict

from django.conf import settings

from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


class BasePagination(PageNumberPagination):
    page_query_param = 'page'
    page_size_query_param = 'count'

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class ResultSetPagination(BasePagination):
    page_size = settings.REST_PAGE_COUNT
    max_page_size = 1000

class ResultNoPagination(BasePagination):

    def paginate_queryset(self, queryset, request, view = None):
        self.request = request
        self.queryset = queryset
        return list(self.queryset)

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.queryset.count()),
            ('results', data)
        ]))

class TestResultSetPagination(BasePagination):
    page_size = 5
    max_page_size = 10