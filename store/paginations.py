from rest_framework.pagination import PageNumberPagination

class DefaultPagination(PageNumberPagination):
    paage_size = 10