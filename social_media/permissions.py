from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Profile


class IsOwnerOrReadOnly(BasePermission):
    """Allow to create/update/partial update/delete only to it's owner"""

    def has_object_permission(self, request, view, obj):
        print(type(obj))
        if request.method in SAFE_METHODS:
            return True

        elif request.user.is_authenticated:
            if isinstance(obj, Profile) and request.user == obj.user:
                return True
            return request.user == obj.author.user

