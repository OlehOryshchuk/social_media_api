from django.urls.base import reverse_lazy

from rest_framework.response import Response
from rest_framework import status

from djoser.views import UserViewSet as DjoserUserViewSet
from djoser.email import PasswordResetEmail as DjoserPasswordResetEmail


class UserViewSet(DjoserUserViewSet):
    """Unable list endpoint from DjoserUserViewSet"""
    def list(self, request, *args, **kwargs):
        return Response(status=status.HTTP_404_NOT_FOUND)


class PasswordResetEmail(DjoserPasswordResetEmail):
    template_name = "registration/password_reset_email.html"
