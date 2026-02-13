from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per hour"])


def create_app(config_name="production"):
    app = Flask(__name__, instance_relative_config=True)

    from app.config import config_map

    app.config.from_object(config_map[config_name])

    # Ensure instance folder exists
    import os

    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # Initialize encryption
    from app.services.encryption_service import EncryptionService

    EncryptionService.initialize(app.instance_path)

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.views.dashboard import dashboard_bp
    from app.views.secrets import secrets_bp
    from app.views.folders import folders_bp
    from app.views.admin import admin_bp
    from app.views.audit import audit_bp
    from app.views.generator import generator_bp
    from app.views.oracle_admin import oracle_admin_bp
    from app.views.licenses import licenses_bp
    from app.views.applications import applications_bp
    from app.api.v1 import api_v1_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(secrets_bp)
    app.register_blueprint(folders_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(generator_bp)
    app.register_blueprint(oracle_admin_bp)
    app.register_blueprint(licenses_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(api_v1_bp, url_prefix="/api/v1")

    # Exempt API from CSRF (uses token auth)
    csrf.exempt(api_v1_bp)

    # User loader for flask-login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User

        return db.session.get(User, int(user_id))

    # Make session permanent by default (for timeout)
    @app.before_request
    def make_session_permanent():
        from flask import session

        session.permanent = True

    # Error logging for production
    import logging

    log_dir = os.path.join(os.path.dirname(app.root_path), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app_error.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.addHandler(file_handler)

    return app
