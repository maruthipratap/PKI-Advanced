from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """
    Usage:
        @role_required('ca_admin')
        @role_required('ca_admin', 'server_admin')
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in.', 'error')
                return redirect(url_for('auth.login'))
            if current_user.role_name not in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('portal.landing'))
            return f(*args, **kwargs)
        return decorated
    return decorator