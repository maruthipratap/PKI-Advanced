from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user
from app import db
from app.auth.decorators import login_required
from app.models.certificate_db import Certificate
from app.audit.logger import log_action

renew_bp = Blueprint('renew', __name__)


def get_expiring_soon(days=30):
    """Return active certs expiring within given days."""
    from datetime import timedelta
    cutoff = datetime.utcnow() + timedelta(days=days)
    return Certificate.query.filter(
        Certificate.status == 'ACTIVE',
        Certificate.valid_to <= cutoff,
        Certificate.valid_to >= datetime.utcnow()
    ).all()


@renew_bp.route('/renew/<int:cert_id>', methods=['POST'])
@login_required
def renew_certificate(cert_id):
    old_cert = Certificate.query.get_or_404(cert_id)

    # Only owner or CA admin can renew
    is_owner    = old_cert.owner_name == current_user.username
    is_ca_admin = current_user.is_ca_admin()

    if not is_owner and not is_ca_admin:
        flash('You do not have permission to renew this certificate.', 'error')
        return redirect(url_for('portal.user_portal'))

    if old_cert.status == 'REVOKED':
        flash('Revoked certificates cannot be renewed.', 'error')
        return redirect(url_for('verify.view_cert', cert_id=cert_id))

    try:
        from app.ca.certificate import issue_certificate

        # Issue new certificate with same details
        cert_pem, serial, valid_from, valid_to = issue_certificate(
            old_cert.owner_name,
            old_cert.email,
            old_cert.organization
        )

        # Mark old cert as revoked (superseded)
        from app.models.certificate_db import RevokedCertificate
        old_cert.status = 'REVOKED'
        revoked = RevokedCertificate(
            serial_number = old_cert.serial_number,
            owner_name    = old_cert.owner_name,
            reason        = 'Superseded — renewed by user'
        )
        db.session.add(revoked)

        # Save new cert
        new_cert = Certificate(
            serial_number = serial,
            owner_name    = old_cert.owner_name,
            email         = old_cert.email,
            organization  = old_cert.organization,
            issued_by     = 'PKI-Advanced Intermediate CA',
            valid_from    = valid_from,
            valid_to      = valid_to,
            cert_pem      = cert_pem,
            status        = 'ACTIVE'
        )
        db.session.add(new_cert)
        db.session.commit()

        # Regenerate CRL since old cert is now revoked
        try:
            from app.revocation.crl_manager import generate_crl
            generate_crl()
        except Exception as e:
            print(f"  [CRL] Warning: {e}")

        log_action(
            'CERT_RENEWED',
            detail=f'Renewed certificate for {old_cert.owner_name}',
            certificate_serial=serial
        )

        flash(f'Certificate renewed successfully! New cert valid until {valid_to.strftime("%Y-%m-%d")}.', 'success')
        return redirect(url_for('verify.view_cert', cert_id=new_cert.id))

    except Exception as e:
        db.session.rollback()
        flash(f'Error renewing certificate: {str(e)}', 'error')
        return redirect(url_for('verify.view_cert', cert_id=cert_id))