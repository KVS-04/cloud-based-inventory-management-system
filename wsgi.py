"""
P5. Cloud-based Inventory Management System
============================================
WSGI entry point for production deployment (Gunicorn / Azure App Service).

Usage:
    gunicorn wsgi:app --bind 0.0.0.0:8000 --workers 4
"""

from app import create_app

# Create the application instance for WSGI servers
app = create_app()
