from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from app.auth.decorators import login_required

portal_bp = Blueprint('portal', __name__)


@portal_bp.route('/')
def landing():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return render_template('portal/landing.html')


@portal_bp.route('/portal/user')
@login_required
def user_portal():
    from app.requests.models import CertificateRequest
    my_requests = CertificateRequest.query.filter_by(
        user_id=current_user.id
    ).order_by(CertificateRequest.requested_at.desc()).all()
    return render_template('portal/user.html', my_requests=my_requests)


@portal_bp.route('/portal/ca')
@login_required
def ca_portal():
    if not current_user.is_ca_admin():
        from flask import flash
        flash('CA Admin access required.', 'error')
        return redirect(url_for('portal.landing'))

    from app.requests.models import CertificateRequest
    from app.models.certificate_db import Certificate

    pending  = CertificateRequest.query.filter_by(status='PENDING').all()
    all_certs = Certificate.query.order_by(Certificate.issued_at.desc()).all()
    return render_template('portal/ca_admin.html',
        pending=pending, all_certs=all_certs
    )