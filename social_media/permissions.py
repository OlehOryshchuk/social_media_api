from rest_framework.permissions import BasePermission, SAFE_METHODS

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

