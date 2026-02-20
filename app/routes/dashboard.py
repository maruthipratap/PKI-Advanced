from flask import Blueprint, render_template
from app.models.certificate_db import Certificate

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    total    = Certificate.query.count()
    active   = Certificate.query.filter_by(status='ACTIVE').count()
    revoked  = Certificate.query.filter_by(status='REVOKED').count()
    recent   = Certificate.query.order_by(Certificate.issued_at.desc()).limit(5).all()

    return render_template('dashboard.html',
        total=total, active=active, revoked=revoked, recent=recent
    )