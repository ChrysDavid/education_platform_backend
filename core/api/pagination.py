from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.response import Response
from collections import OrderedDict

from ..utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

class StandardResultsSetPagination(PageNumberPagination):
    """
    Pagination standard par numéro de page.
    """
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = MAX_PAGE_SIZE
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page_size', self.get_page_size(self.request)),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('results', data)
        ]))

class LargeResultsSetPagination(PageNumberPagination):
    """
    Pagination pour les grands ensembles de données.
    """
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class SmallResultsSetPagination(PageNumberPagination):
    """
    Pagination pour les petits ensembles de données.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

class FlexiblePagination(LimitOffsetPagination):
    """
    Pagination flexible avec limite et décalage.
    """
    default_limit = DEFAULT_PAGE_SIZE
    max_limit = MAX_PAGE_SIZE
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('limit', self.limit),
            ('offset', self.offset),
            ('results', data)
        ]))