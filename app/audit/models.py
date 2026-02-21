# app/audit/models.py
from datetime import datetime
from app import db


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id                 = db.Column(db.Integer,     primary_key=True)
    user_id            = db.Column(db.Integer,     db.ForeignKey('users.id'), nullable=True)
    username           = db.Column(db.String(80),  nullable=True)   # stored directly in case user deleted
    action             = db.Column(db.String(128), nullable=False)
    detail             = db.Column(db.String(512), nullable=True)
    certificate_serial = db.Column(db.String(64),  nullable=True)
    ip_address         = db.Column(db.String(64),  nullable=True)
    timestamp          = db.Column(db.DateTime,    default=datetime.utcnow)
    status             = db.Column(db.String(16),  default='SUCCESS')  # SUCCESS / FAILED

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.username} at {self.timestamp}>"