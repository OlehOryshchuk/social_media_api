from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import (
    BasePermission,
    SAFE_METHODS,
    IsAuthenticated
)

from .models import Profile


class IsOwnerOrReadOnly(BasePermission):
    """Allow to create/update/partial update/delete only to it's owner"""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        elif request.user.is_authenticated:
            if isinstance(obj, Profile):
                if request.user == obj.user:
                    return True
                return False
            return request.user == obj.author.user


class IsAuthenticatedAndUserHaveProfile(IsAuthenticated):
    message = {"error": "You must be authenticated and have profile to perform this action"}

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)

        if is_authenticated and not hasattr(request.user, "profile"):
            raise PermissionDenied(self.message)
        return is_authenticated
