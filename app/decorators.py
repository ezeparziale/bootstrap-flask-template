from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user

from .models import Permission


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(f):
    return permission_required(Permission.ADMIN)(f)


def password_not_expired(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return abort(401)
        if current_user.password_is_expired():
            flash("Your password has expired. Please change it.", "danger")
            return redirect(url_for("account.change_password"))
        return f(*args, **kwargs)

    return decorated_function
