from collections import OrderedDict

from django.conf import settings
from rest_framework.pagination import PageNumberPagination

from .response import EncryptedResponse


class BasePagination(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "count"

    def get_paginated_response(self, data, user=None):
        return EncryptedResponse(
            data=OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            ),
            user=user,
        )


class ResultSetPagination(BasePagination):
    page_size = settings.REST_PAGE_COUNT
    max_page_size = 1000


class ResultNoPagination(BasePagination):
    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        self.queryset = queryset
        return list(self.queryset)

    def get_paginated_response(self, data, user=None):
        return EncryptedResponse(data=OrderedDict([("count", self.queryset.count()), ("results", data)]), user=user)
