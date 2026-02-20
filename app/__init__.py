from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    # Ensure storage directories exist
    import os
    for folder in [
        Config.ROOT_CA_DIR,
        Config.INTERMEDIATE_DIR,
        Config.ISSUED_DIR
    ]:
        os.makedirs(folder, exist_ok=True)

    # Register blueprints (routes)
    from app.routes.dashboard import dashboard_bp
    from app.routes.issue     import issue_bp
    from app.routes.verify    import verify_bp
    from app.routes.revoke    import revoke_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(issue_bp)
    app.register_blueprint(verify_bp)
    app.register_blueprint(revoke_bp)

    # Create DB tables if they don't exist
    with app.app_context():
        from app.models import certificate_db
        db.create_all()

    return app