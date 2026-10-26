from rest_framework import permissions
from accounts.models import UserRole


class IsCandidate(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.CANDIDATE)


class IsRecruiter(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and 
            (request.user.role == UserRole.RECRUITER or request.user.role == UserRole.SUPER_ADMIN or request.user.is_staff)
        )


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and 
            (request.user.role == UserRole.SUPER_ADMIN or request.user.is_superuser)
        )
