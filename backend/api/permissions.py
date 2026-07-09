from rest_framework.permissions import BasePermission


class IsReviewer(BasePermission):
    """Reviewer/admin pages are gated on ``is_staff``.

    We deliberately keep permissions minimal for v0: a reviewer is simply any
    user with the Django ``is_staff`` flag (set via the admin or createsuperuser).
    This cleanly separates normal user pages from reviewer pages without
    building a full roles system yet.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)
