"""
P5. Cloud-based Inventory Management System
============================================
Flask extensions initialization.

Extensions are initialized here and attached to the app in create_app().
"""

from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS

# --- Flask-Login: Session-based authentication ---
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# --- CSRF Protection ---
csrf = CSRFProtect()

# --- CORS for API endpoints ---
cors = CORS()
