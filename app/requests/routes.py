from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from app import db
from app.auth.decorators import login_required, role_required
from app.requests.models import CertificateRequest
from app.audit.logger import log_action

requests_bp = Blueprint('requests', __name__)


@requests_bp.route('/request', methods=['GET', 'POST'])
@login_required
def submit_request():
    if request.method == 'POST':
        owner_name   = request.form.get('owner_name', '').strip()
        email        = request.form.get('email', '').strip()
        organization = request.form.get('organization', '').strip()
        purpose      = request.form.get('purpose', '').strip()

        if not owner_name:
            flash('Owner name is required.', 'error')
            return redirect(url_for('requests.submit_request'))

        # Check for existing pending request
        existing = CertificateRequest.query.filter_by(
            user_id=current_user.id, status='PENDING'
        ).first()
        if existing:
            flash('You already have a pending certificate request.', 'error')
            return redirect(url_for('portal.user_portal'))

        new_req = CertificateRequest(
            user_id      = current_user.id,
            owner_name   = owner_name,
            email        = email or None,
            organization = organization or None,
            purpose      = purpose or None,
            status       = 'PENDING'
        )
        db.session.add(new_req)
        db.session.commit()

        log_action('CERT_REQUEST_SUBMITTED',
            detail=f'Certificate requested for {owner_name}'
        )
        flash('Certificate request submitted! Awaiting CA Admin approval.', 'success')
        return redirect(url_for('portal.user_portal'))

    return render_template('requests/submit.html')


@requests_bp.route('/requests/review')
@role_required('ca_admin')
def review_requests():
    pending  = CertificateRequest.query.filter_by(status='PENDING').all()
    all_reqs = CertificateRequest.query.order_by(
        CertificateRequest.requested_at.desc()
    ).all()
    return render_template('requests/review.html',
        pending=pending, all_reqs=all_reqs
    )


@requests_bp.route('/requests/approve/<int:req_id>', methods=['POST'])
@role_required('ca_admin')
def approve_request(req_id):
    req = CertificateRequest.query.get_or_404(req_id)

    if req.status != 'PENDING':
        flash('This request is no longer pending.', 'error')
        return redirect(url_for('requests.review_requests'))

    try:
        from app.ca.certificate import issue_certificate
        from app.models.certificate_db import Certificate

        cert_pem, serial, valid_from, valid_to = issue_certificate(
            req.owner_name, req.email, req.organization
        )

        new_cert = Certificate(
            serial_number = serial,
            owner_name    = req.owner_name,
            email         = req.email,
            organization  = req.organization,
            issued_by     = "PKI-Advanced Intermediate CA",
            valid_from    = valid_from,
            valid_to      = valid_to,
            cert_pem      = cert_pem,
            status        = 'ACTIVE'
        )
        db.session.add(new_cert)
        db.session.flush()

        req.status       = 'APPROVED'
        req.reviewed_at  = datetime.utcnow()
        req.reviewed_by  = current_user.username
        req.certificate_id = new_cert.id

        db.session.commit()

        log_action('CERT_APPROVED',
            detail=f'Approved request for {req.owner_name}',
            certificate_serial=serial
        )
        flash(f'Certificate approved and issued for {req.owner_name}.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error issuing certificate: {str(e)}', 'error')

    return redirect(url_for('requests.review_requests'))


@requests_bp.route('/requests/reject/<int:req_id>', methods=['POST'])
@role_required('ca_admin')
def reject_request(req_id):
    req    = CertificateRequest.query.get_or_404(req_id)
    reason = request.form.get('reason', 'No reason provided').strip()

    req.status        = 'REJECTED'
    req.reviewed_at   = datetime.utcnow()
    req.reviewed_by   = current_user.username
    req.reject_reason = reason

    db.session.commit()

    log_action('CERT_REJECTED',
        detail=f'Rejected request for {req.owner_name}. Reason: {reason}'
    )
    flash(f'Request rejected for {req.owner_name}.', 'success')
    return redirect(url_for('requests.review_requests'))