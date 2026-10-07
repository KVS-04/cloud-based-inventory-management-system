"""
Authentication and authorization decorators.
"""

import functools
import jwt
from flask import request, jsonify, current_app, abort, flash, redirect, url_for
from flask_login import current_user, login_required


def role_required(*roles):
    """Decorator to check if the current user has the required role.
    Usage: @role_required('admin', 'manager')
    """
    def decorator(f):
        @functools.wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Shortcut decorator for admin-only access."""
    return role_required('admin')(f)


def manager_required(f):
    """Shortcut decorator for admin and manager access."""
    return role_required('admin', 'manager')(f)


def login_required_api(f):
    """JWT-based authentication decorator for API endpoints."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for JWT token in Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        # Also support session-based auth for API calls from the frontend
        if current_user.is_authenticated:
            return f(*args, **kwargs)

        if not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'message': 'Missing or invalid authorization token.'
            }), 401

        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            # Attach user info to request
            request.jwt_user_id = payload.get('user_id')
            request.jwt_user_role = payload.get('role')
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'message': 'Token has expired.'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'message': 'Invalid token.'
            }), 401

        return f(*args, **kwargs)
    return decorated_function


def api_role_required(*roles):
    """Role check decorator for API endpoints."""
    def decorator(f):
        @functools.wraps(f)
        @login_required_api
        def decorated_function(*args, **kwargs):
            # Check session user role
            if current_user.is_authenticated:
                if current_user.role not in roles:
                    return jsonify({
                        'success': False,
                        'message': 'Insufficient permissions.'
                    }), 403
            else:
                # Check JWT role
                if getattr(request, 'jwt_user_role', None) not in roles:
                    return jsonify({
                        'success': False,
                        'message': 'Insufficient permissions.'
                    }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def api_admin_required(f):
    """Admin-only API decorator."""
    return api_role_required('admin')(f)


def api_manager_required(f):
    """Admin + Manager API decorator."""
    return api_role_required('admin', 'manager')(f)
