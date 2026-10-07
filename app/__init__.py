"""
P5. Cloud-based Inventory Management System
============================================
Flask Application Factory.
"""

import os
from flask import Flask, render_template, redirect, url_for
from flask_login import current_user

from .config import get_config
from .extensions import login_manager, csrf, cors


def create_app(config_class=None):
    """Application factory function."""
    app = Flask(__name__, static_folder='static', template_folder='templates')

    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_context_processors(app)
    _init_aws_services(app)
    _register_user_loader(app)

    return app


def _init_extensions(app):
    """Initialize Flask extensions with the app."""
    login_manager.init_app(app)
    csrf.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})


def _register_blueprints(app):
    """Register all application blueprints."""
    
    # UI Routes
    from .routes.auth import bp as auth_bp
    from .routes.dashboard import bp as dashboard_bp
    from .routes.products import bp as products_bp
    from .routes.inventory import bp as inventory_bp
    
    from .routes.orders import po_bp, so_bp, ret_bp, sup_bp, wh_bp
    from .routes.admin import reports_bp, users_bp, notif_bp, audit_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(inventory_bp)
    
    app.register_blueprint(po_bp)
    app.register_blueprint(so_bp)
    app.register_blueprint(ret_bp)
    app.register_blueprint(sup_bp)
    app.register_blueprint(wh_bp)

    app.register_blueprint(reports_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(notif_bp)
    app.register_blueprint(audit_bp)

    # API Route
    from .api.routes import api_bp
    csrf.exempt(api_bp)
    app.register_blueprint(api_bp)

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))


def _register_error_handlers(app):
    """Register custom error handlers."""
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500


def _register_context_processors(app):
    """Register template context processors for global template variables."""
    @app.context_processor
    def inject_globals():
        return {
            'app_name': 'Cloud Inventory Management',
            'app_version': '1.0.0',
            'current_year': 2026
        }


def _init_aws_services(app):
    """Initialize Azure service clients and store them on the app."""
    if not app.config.get('dynamodb_ENDPOINT'):
        app.logger.warning('dynamodb_ENDPOINT not configured.')

    if not app.config.get('AWS_ACCESS_KEY_ID'):
        app.logger.warning('AWS_ACCESS_KEY_ID not configured.')

    if not app.config.get('AWS_REGION'):
        app.logger.warning('AWS_REGION not configured.')


def _register_user_loader(app):
    """Register the user loader callback for Flask-Login."""
    @login_manager.user_loader
    def load_user(user_id):
        from .services.auth_service import get_user_by_id
        return get_user_by_id(user_id)
