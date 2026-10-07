"""
P5. Cloud-based Inventory Management System
============================================
Application configuration loaded from environment variables.

All AWS credentials and application settings are configured via .env file.
See .env.example for required variables.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""

    # --- Flask Core ---
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False

    # --- JWT ---
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-dev-secret-change-this')
    JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 24))
    JWT_EXPIRATION_DELTA = timedelta(hours=JWT_EXPIRATION_HOURS)

    # --- Session ---
    SESSION_LIFETIME_HOURS = int(os.environ.get('SESSION_LIFETIME_HOURS', 24))
    PERMANENT_SESSION_LIFETIME = timedelta(hours=SESSION_LIFETIME_HOURS)

    # --- Application Settings ---
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 25))
    MAX_UPLOAD_SIZE_MB = int(os.environ.get('MAX_UPLOAD_SIZE_MB', 10))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_MB * 1024 * 1024  # Convert to bytes
    ALLOWED_EXTENSIONS = set(
        os.environ.get('ALLOWED_EXTENSIONS', 'png,jpg,jpeg,gif,webp').split(',')
    )

    # --- Admin Default Account ---
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@inventory.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin@123')
    ADMIN_FIRST_NAME = os.environ.get('ADMIN_FIRST_NAME', 'System')
    ADMIN_LAST_NAME = os.environ.get('ADMIN_LAST_NAME', 'Administrator')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    FLASK_ENV = 'production'


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True


# Configuration dictionary for easy access
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get the configuration class based on FLASK_ENV environment variable."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)
