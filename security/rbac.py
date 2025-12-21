"""
Role-Based Access Control implementation
"""
from domain.roles.role import Role
from utils.exceptions import UnauthorizedAccessError
from functools import wraps
from flask import session


def require_role(*allowed_roles: Role):
    """Decorator to require specific roles"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_role = session.get('user_role')
            if not user_role:
                raise UnauthorizedAccessError("User not authenticated")
            
            role = Role(user_role)
            if role not in allowed_roles:
                raise UnauthorizedAccessError(
                    f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user_role() -> Role:
    """Get current user's role from session"""
    user_role = session.get('user_role')
    if not user_role:
        return Role.CUSTOMER  # Default
    return Role(user_role)


def get_current_user_id() -> str:
    """Get current user ID from session"""
    return session.get('user_id', 'guest')

