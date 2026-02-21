# app/requests/models.py
from datetime import datetime
from app import db


class CertificateRequest(db.Model):
    __tablename__ = 'certificate_requests'

    id           = db.Column(db.Integer,     primary_key=True)
    user_id      = db.Column(db.Integer,     db.ForeignKey('users.id'), nullable=False)
    owner_name   = db.Column(db.String(128), nullable=False)
    email        = db.Column(db.String(256), nullable=True)
    organization = db.Column(db.String(256), nullable=True)
    purpose      = db.Column(db.String(512), nullable=True)
    status       = db.Column(db.String(16),  default='PENDING')
    # PENDING / APPROVED / REJECTED / REVOKED

    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at  = db.Column(db.DateTime, nullable=True)
    reviewed_by  = db.Column(db.String(80), nullable=True)  # CA admin username
    reject_reason= db.Column(db.String(512), nullable=True)

    # Link to issued certificate (set after approval)
    certificate_id = db.Column(db.Integer, db.ForeignKey('certificates.id'), nullable=True)

    def __repr__(self):
        return f"<CertReq {self.owner_name} | {self.status}>"