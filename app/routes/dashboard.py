from flask import Blueprint, render_template, request
from app.models.certificate_db import Certificate
from app.auth.decorators import login_required, role_required
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    total   = Certificate.query.count()
    active  = Certificate.query.filter_by(status='ACTIVE').count()
    revoked = Certificate.query.filter_by(status='REVOKED').count()
    recent  = Certificate.query.order_by(Certificate.issued_at.desc()).limit(5).all()
    return render_template('dashboard.html',
        total=total, active=active, revoked=revoked, recent=recent
    )


@dashboard_bp.route('/certificates')
@login_required
def list_certs():
    # Filter param from query string: ?filter=active / expired / revoked / all
    f = request.args.get('filter', 'all')
    now = datetime.utcnow()

    query = Certificate.query

    if f == 'active':
        query = query.filter(
            Certificate.status == 'ACTIVE',
            Certificate.valid_to >= now
        )
    elif f == 'revoked':
        query = query.filter_by(status='REVOKED')
    elif f == 'expired':
        query = query.filter(
            Certificate.status == 'ACTIVE',
            Certificate.valid_to < now
        )

    certs = query.order_by(Certificate.issued_at.desc()).all()

    # Counts for filter tabs
    counts = {
        'all':     Certificate.query.count(),
        'active':  Certificate.query.filter(Certificate.status=='ACTIVE', Certificate.valid_to>=now).count(),
        'revoked': Certificate.query.filter_by(status='REVOKED').count(),
        'expired': Certificate.query.filter(Certificate.status=='ACTIVE', Certificate.valid_to<now).count(),
    }

    return render_template('certificates.html',
        certs=certs, active_filter=f, counts=counts
    )


@dashboard_bp.route('/audit')
@role_required('ca_admin')
def audit_log():
    from app.audit.models import AuditLog
    # Filter by action type
    action_filter = request.args.get('action', 'all')
    query = AuditLog.query

    if action_filter != 'all':
        query = query.filter(AuditLog.action.like(f'%{action_filter.upper()}%'))

    logs = query.order_by(AuditLog.timestamp.desc()).limit(200).all()

    # Distinct action types for filter dropdown
    all_actions = db.session.query(AuditLog.action).distinct().all()

    return render_template('audit.html',
        logs=logs, active_filter=action_filter,
        all_actions=[a[0] for a in all_actions]
    )


# Import db for audit route
from app import db