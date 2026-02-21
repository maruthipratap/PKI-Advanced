from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config

db           = SQLAlchemy()
login_manager = LoginManager()
bcrypt        = Bcrypt()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'error'

    # Storage dirs
    import os
    for folder in [Config.ROOT_CA_DIR, Config.INTERMEDIATE_DIR, Config.ISSUED_DIR]:
        os.makedirs(folder, exist_ok=True)

    # User loader for flask-login
    from app.auth.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.auth.routes        import auth_bp
    from app.routes.portal      import portal_bp
    from app.routes.dashboard   import dashboard_bp
    from app.routes.issue       import issue_bp
    from app.routes.verify      import verify_bp
    from app.routes.revoke      import revoke_bp
    from app.routes.crl_ocsp    import crl_ocsp_bp
    from app.requests.routes    import requests_bp
    from app.routes.renew       import renew_bp
    from app.routes.admin       import admin_bp

    app.register_blueprint(renew_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(issue_bp)
    app.register_blueprint(verify_bp)
    app.register_blueprint(revoke_bp)
    app.register_blueprint(crl_ocsp_bp)
    app.register_blueprint(requests_bp)

    with app.app_context():
        # Import all models so SQLAlchemy sees them
        from app.models.certificate_db import Certificate, RevokedCertificate
        from app.auth.models           import User, Role
        from app.audit.models          import AuditLog
        from app.requests.models       import CertificateRequest

        db.create_all()

        # Seed default roles
        _seed_roles()

        # Seed default CA admin account
        _seed_admin()

        # CA hierarchy
        from app.ca.root_ca         import generate_root_ca
        from app.ca.intermediate_ca import generate_intermediate_ca
        print("\n[STARTUP] Initializing CA hierarchy...")
        generate_root_ca()
        generate_intermediate_ca()
        print("[STARTUP] CA hierarchy ready!\n")

    return app


def _seed_roles():
    """Create roles if they don't exist."""
    from app.auth.models import Role
    for role_name in ['user', 'server_admin', 'ca_admin']:
        if not Role.query.filter_by(name=role_name).first():
            db.session.add(Role(name=role_name))
    db.session.commit()


def _seed_admin():
    """Create default CA admin account if none exists."""
    from app.auth.models import User, Role
    if not User.query.filter_by(username='admin').first():
        ca_role  = Role.query.filter_by(name='ca_admin').first()
        admin    = User(
            username = 'admin',
            email    = 'admin@pki-advanced.local',
            role     = ca_role,
            is_active= True
        )
        admin.set_password('Admin@12345')
        db.session.add(admin)
        db.session.commit()
        print("  [SEED] Default CA admin created → username: admin / password: Admin@12345")
        print("  [SEED] Change this password after first login!\n")