from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models.certificate_db import Certificate, RevokedCertificate
from app.revocation.crl_manager import generate_crl

revoke_bp = Blueprint('revoke', __name__)

@revoke_bp.route('/revoke', methods=['GET', 'POST'])
def revoke():
    if request.method == 'POST':
        owner_name = request.form.get('owner_name', '').strip()
        reason     = request.form.get('reason', 'No reason provided').strip()

        cert = Certificate.query.filter_by(
            owner_name=owner_name, status='ACTIVE'
        ).first()

        if not cert:
            flash(f'No active certificate found for {owner_name}.', 'error')
            return redirect(url_for('revoke.revoke'))

        # Mark as revoked in certificates table
        cert.status = 'REVOKED'

        # Add to revocation log
        revoked = RevokedCertificate(
            serial_number = cert.serial_number,
            owner_name    = owner_name,
            reason        = reason
        )
        db.session.add(revoked)
        db.session.commit()

        try:
            generate_crl()
        except Exception as e:
            print(f"  [CRL] Warning: could not regenerate CRL: {e}")
        flash(f'Certificate revoked for {owner_name}.', 'success')
        return redirect(url_for('dashboard.index'))

    # Show all active certs in dropdown
    active_certs = Certificate.query.filter_by(status='ACTIVE').all()
    return render_template('revoke.html', active_certs=active_certs)