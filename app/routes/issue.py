from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.ca.certificate import issue_certificate
from app.models.certificate_db import Certificate

issue_bp = Blueprint('issue', __name__)

@issue_bp.route('/issue', methods=['GET', 'POST'])
def issue():
    if request.method == 'POST':
        owner_name   = request.form.get('owner_name', '').strip()
        email        = request.form.get('email', '').strip()
        organization = request.form.get('organization', '').strip()

        if not owner_name:
            flash('Owner name is required.', 'error')
            return redirect(url_for('issue.issue'))

        # Check if already issued and active
        existing = Certificate.query.filter_by(
            owner_name=owner_name, status='ACTIVE'
        ).first()
        if existing:
            flash(f'Active certificate already exists for {owner_name}.', 'error')
            return redirect(url_for('issue.issue'))

        try:
            cert_pem, serial, valid_from, valid_to = issue_certificate(
                owner_name, email or None, organization or None
            )

            new_cert = Certificate(
                serial_number = serial,
                owner_name    = owner_name,
                email         = email or None,
                organization  = organization or None,
                issued_by     = "PKI-Advanced Intermediate CA",
                valid_from    = valid_from,
                valid_to      = valid_to,
                cert_pem      = cert_pem,
                status        = 'ACTIVE'
            )
            db.session.add(new_cert)
            db.session.commit()

            flash(f'Certificate issued successfully for {owner_name}!', 'success')
            return redirect(url_for('verify.view_cert', cert_id=new_cert.id))

        except Exception as e:
            flash(f'Error issuing certificate: {str(e)}', 'error')
            return redirect(url_for('issue.issue'))

    return render_template('issue.html')