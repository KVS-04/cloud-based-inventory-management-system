"""
P5. Cloud-based Inventory Management System
============================================
Application entry point for development server.
"""

from app import create_app

# Create the Flask application instance using the app factory
app = create_app()

if __name__ == '__main__':
    # Run the development server
    # In production, use gunicorn or Azure App Service
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config.get('DEBUG', False)
    )
