from flask import Blueprint, render_template
from app.models.certificate_db import Certificate
from app.auth.decorators import login_required, role_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    total   = Certificate.query.count()
    active  = Certificate.query.filter_by(status='ACTIVE').count()
    revoked = Certificate.query.filter_by(status='REVOKED').count()
    recent  = Certificate.query.order_by(Certificate.issued_at.desc()).limit(5).all()
    return render_template('dashboard.html', total=total, active=active, revoked=revoked, recent=recent)


@dashboard_bp.route('/audit')
@role_required('ca_admin')
def audit_log():
    from app.audit.models import AuditLog
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(200).all()
    return render_template('audit.html', logs=logs)