# permissions.py
from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Custom permission to only allow users to update or delete their own data.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user is trying to update or delete their own data
        return obj.id == request.user.id
    


class IsAdmin(BasePermission):
    """
    Allows access to mid-level users for GET, POST..
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            # Check if the user is an admin or staff of the company associated with the object
            if request.user.role in ['admin', 'staff'] and obj.company == request.user.company:
                return True
        return False
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.role == 'admin':
            return request.method in ['GET', 'POST','PUT','DELETE']
        return False
    
# class IsStaff(BasePermission):
#     """
#     Allows access to staff users for GET, POST..
#     """
# class IsCompanyStaff(BasePermission):
#     def has_object_permission(self, request, view, obj):
#         # Check if the user belongs to the same company as the object
#         return obj.company == request.user.company

class IsCustomer(BasePermission):
    """
    Allows access to regular users for GET and POST requests.
    """
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.role == 'customer':
            return request.method in ['GET', 'POST']
        return False

# class IsCustomerOrAdminOrSuperuser(BasePermission):
#     """
#     Allows access to users who are either 'customer' or 'administrator'.
#     """
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and (
#             request.user.role == 'customer' or request.user.role == 'admin' or request.user.is_staff
#         )
    

class IsAdminOrSuperuser(BasePermission):
    """
    Allows access to users who are either 'customer' or 'administrator'.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Check if the user is an admin or superuser
        return request.user.role in ['admin', 'staff'] or request.user.is_superuser