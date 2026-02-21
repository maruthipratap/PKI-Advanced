from flask import request as flask_request
from flask_login import current_user
from app import db
from app.audit.models import AuditLog


def log_action(action, detail=None, certificate_serial=None, status='SUCCESS', user=None):
    """
    Call this everywhere something important happens.
    Usage:
        log_action("CERTIFICATE_ISSUED", detail="Issued for John", certificate_serial="12345")
        log_action("LOGIN_FAILED", detail="Bad password", status="FAILED")
    """
    try:
        # Determine who is acting
        actor = user or (current_user if current_user.is_authenticated else None)

        log = AuditLog(
            user_id            = actor.id       if actor else None,
            username           = actor.username if actor else 'anonymous',
            action             = action,
            detail             = detail,
            certificate_serial = certificate_serial,
            ip_address         = flask_request.remote_addr,
            status             = status
        )
        db.session.add(log)
        db.session.commit()

    except Exception as e:
        print(f"  [AUDIT] Warning: could not write audit log: {e}")