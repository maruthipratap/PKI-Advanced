from datetime import datetime
from flask_login import UserMixin
from flask_bcrypt import generate_password_hash, check_password_hash
from app import db


class Role(db.Model):
    __tablename__ = 'roles'

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    # user / server_admin / ca_admin

    users = db.relationship('User', backref='role', lazy=True)

    def __repr__(self):
        return f"<Role {self.name}>"


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80),  unique=True, nullable=False)
    email        = db.Column(db.String(256), unique=True, nullable=False)
    password     = db.Column(db.String(256), nullable=False)
    role_id      = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    is_active    = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    last_login   = db.Column(db.DateTime, nullable=True)

    # Relationships
    requests     = db.relationship('CertificateRequest', backref='requester', lazy=True)
    audit_logs   = db.relationship('AuditLog', backref='actor', lazy=True)

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password).decode('utf-8')

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    @property
    def role_name(self):
        return self.role.name if self.role else None

    def is_ca_admin(self):
        return self.role_name == 'ca_admin'

    def is_server_admin(self):
        return self.role_name == 'server_admin'

    def is_user(self):
        return self.role_name == 'user'

    def __repr__(self):
        return f"<User {self.username} | {self.role_name}>"