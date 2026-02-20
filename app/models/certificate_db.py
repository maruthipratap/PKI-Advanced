from datetime import datetime
from app import db


class Certificate(db.Model):
    __tablename__ = 'certificates'

    id            = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(64),  unique=True, nullable=False)
    owner_name    = db.Column(db.String(128), nullable=False)
    email         = db.Column(db.String(256), nullable=True)
    organization  = db.Column(db.String(256), nullable=True)
    issued_by     = db.Column(db.String(128), nullable=False)
    issued_at     = db.Column(db.DateTime,    default=datetime.utcnow)
    valid_from    = db.Column(db.DateTime,    nullable=False)
    valid_to      = db.Column(db.DateTime,    nullable=False)
    status        = db.Column(db.String(16),  default='ACTIVE')   # ACTIVE / REVOKED
    cert_pem      = db.Column(db.Text,        nullable=False)      # full PEM stored in DB

    def is_expired(self):
        return datetime.utcnow() > self.valid_to

    def is_valid(self):
        return self.status == 'ACTIVE' and not self.is_expired()

    def __repr__(self):
        return f"<Certificate {self.owner_name} | {self.status}>"


class RevokedCertificate(db.Model):
    __tablename__ = 'revoked_certificates'

    id            = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(64),  nullable=False)
    owner_name    = db.Column(db.String(128), nullable=False)
    revoked_at    = db.Column(db.DateTime,    default=datetime.utcnow)
    reason        = db.Column(db.String(256), nullable=True)

    def __repr__(self):
        return f"<Revoked {self.owner_name} at {self.revoked_at}>"