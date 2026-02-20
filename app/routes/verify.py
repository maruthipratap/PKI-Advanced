from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.certificate_db import Certificate

verify_bp = Blueprint('verify', __name__)

@verify_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    result = None
    if request.method == 'POST':
        owner_name = request.form.get('owner_name', '').strip()
        cert = Certificate.query.filter_by(owner_name=owner_name).order_by(
            Certificate.issued_at.desc()
        ).first()

        if not cert:
            result = {'status': 'NOT_FOUND', 'owner': owner_name}
        elif cert.status == 'REVOKED':
            result = {'status': 'REVOKED', 'owner': owner_name, 'cert': cert}
        elif cert.is_expired():
            result = {'status': 'EXPIRED', 'owner': owner_name, 'cert': cert}
        else:
            result = {'status': 'VALID', 'owner': owner_name, 'cert': cert}

    return render_template('verify.html', result=result)


@verify_bp.route('/view/<int:cert_id>')
def view_cert(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    return render_template('view.html', cert=cert)


@verify_bp.route('/certificates')
def list_certs():
    certs = Certificate.query.order_by(Certificate.issued_at.desc()).all()
    return render_template('view.html', certs=certs, list_mode=True)