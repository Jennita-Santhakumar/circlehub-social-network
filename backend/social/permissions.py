from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Only the author may edit/delete their own object; everyone authenticated can read."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = getattr(obj, "author", None) or getattr(obj, "user", None)
        return owner == request.user
