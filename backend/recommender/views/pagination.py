from rest_framework.pagination import LimitOffsetPagination

class InfiniteScrollPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 50 