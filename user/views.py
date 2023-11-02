from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from knox.auth import TokenAuthentication

from .serializers import UserSerializer


class CreateUserView(generics.CreateAPIView):
    """Create and save user in Database User table"""
    serializer_class = UserSerializer
