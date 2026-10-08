"""
Shared role-based access control (RBAC) permission classes.
Applied per-view across apps.patients, apps.departments, apps.staff, etc.
Kiosk endpoints deliberately do NOT use these — they are AllowAny + read-only.
"""
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "ADMIN")


class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "DOCTOR")


class IsNurse(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "NURSE")


class IsHospitalAdministrator(BasePermission):
    """Read-only analytics role — must never touch patient-level endpoints."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "HOSPITAL_ADMINISTRATOR"
        )


class IsAdminOrDoctorOrNurse(BasePermission):
    """General clinical-side access: can view queue/patient data for their department."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in {"ADMIN", "DOCTOR", "NURSE"}
        )


class IsAdminOrNurse(BasePermission):
    """Intake creation/updates: nurses do the entry, admins can too."""

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.role in {"ADMIN", "NURSE"}
        )


class IsSameDepartmentOrAdmin(BasePermission):
    """Object-level check: doctors/nurses may only act within their own department."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == "ADMIN":
            return True
        department = getattr(obj, "department", None)
        return department is not None and department == request.user.department
