from django.contrib.auth import get_user_model

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from knox.auth import TokenAuthentication

from .serializers import UserSerializer


class CreateUserView(generics.CreateAPIView):
    """Create and save user in Database User table"""
    serializer_class = UserSerializer


class ManagerUserView(generics.RetrieveUpdateAPIView):
    """Autentication is required. Return current user and
    user can update his credentials"""
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self) -> get_user_model:
        return self.request.user
