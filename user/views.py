from rest_framework.response import Response
from rest_framework import status

from djoser.views import UserViewSet as DjoserUserViewSet


class UserViewSet(DjoserUserViewSet):
    """Unable list endpoint from DjoserUserViewSet"""
    def list(self, request, *args, **kwargs):
        return Response(status=status.HTTP_404_NOT_FOUND)
