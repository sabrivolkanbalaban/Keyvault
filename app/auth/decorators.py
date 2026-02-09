from functools import wraps

from flask import abort
from flask_login import current_user


def role_required(*roles):
    """Decorator to restrict access to specific roles."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(f):
    """Shortcut for @role_required('admin')."""
    return role_required("admin")(f)


def write_required(f):
    """Requires 'admin' or 'user' role (not 'readonly')."""
    return role_required("admin", "user")(f)
