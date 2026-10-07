"""
Authentication service - User authentication, JWT, and user management.
"""

import jwt
import logging
from datetime import datetime, timezone, timedelta
from flask import current_app

from ..models.user import User
from ..services.dynamodb_service import dynamodb
from ..utils.constants import CONTAINER_USERS

logger = logging.getLogger(__name__)


def get_user_by_id(user_id: str) -> User:
    """Retrieve a user by ID from Cosmos DB. Used by Flask-Login user_loader."""
    # DEMO MODE: If using the mock admin ID
    if user_id == 'demo-admin-id':
        demo_user = User(id='demo-admin-id', email='admin@inventory.com', role='admin', first_name='Demo', last_name='Admin')
        demo_user.set_password('Admin@123')
        return demo_user
        
    try:
        # Query across all partitions since we don't know the role
        items = dynamodb.query_items(
            CONTAINER_USERS,
            'SELECT * FROM c WHERE c.id = @id',
            [{'name': '@id', 'value': user_id}]
        )
        if items:
            return User.from_dict(items[0])
        return None
    except Exception as e:
        logger.error(f'Error loading user {user_id}: {e}')
        return None


def get_user_by_email(email: str) -> User:
    """Retrieve a user by email address."""
    # DEMO MODE: allow admin@inventory.com bypass
    if email == 'admin@inventory.com':
        demo_user = User(id='demo-admin-id', email='admin@inventory.com', role='admin', first_name='Demo', last_name='Admin')
        demo_user.set_password('Admin@123')
        return demo_user
        
    try:
        items = dynamodb.query_items(
            CONTAINER_USERS,
            'SELECT * FROM c WHERE c.email = @email',
            [{'name': '@email', 'value': email}]
        )
        if items:
            return User.from_dict(items[0])
        return None
    except Exception as e:
        logger.error(f'Error finding user by email: {e}')
        return None


def authenticate_user(email: str, password: str) -> User:
    """Authenticate user by email and password. Returns User or None."""
    user = get_user_by_email(email)
    if user and user.is_active and user.check_password(password):
        # Update last login
        update_last_login(user.id, user.role)
        return user
    return None


def create_user(data: dict) -> User:
    """Create a new user in Cosmos DB."""
    try:
        user = User(
            email=data.get('email', '').strip().lower(),
            username=data.get('email', '').split('@')[0],
            first_name=data.get('first_name', '').strip(),
            last_name=data.get('last_name', '').strip(),
            phone=data.get('phone', '').strip(),
            role=data.get('role', 'staff'),
            is_active=data.get('is_active', True)
        )
        user.set_password(data.get('password', ''))
        dynamodb.create_item(CONTAINER_USERS, user.to_dict())
        logger.info(f'User created: {user.email}')
        return user
    except Exception as e:
        logger.error(f'Error creating user: {e}')
        raise


def update_user(user_id: str, data: dict) -> User:
    """Update an existing user."""
    try:
        user = get_user_by_id(user_id)
        if not user:
            return None
        old_role = user.role
        if 'first_name' in data:
            user.first_name = data['first_name'].strip()
        if 'last_name' in data:
            user.last_name = data['last_name'].strip()
        if 'phone' in data:
            user.phone = data['phone'].strip()
        if 'role' in data:
            user.role = data['role']
        if 'email' in data:
            user.email = data['email'].strip().lower()
        if 'is_active' in data:
            user.is_active = data['is_active']
        if data.get('password'):
            user.set_password(data['password'])
        user.updated_at = datetime.now(timezone.utc).isoformat()

        # If role changed, delete old and create new (partition key changed)
        if old_role != user.role:
            try:
                dynamodb.delete_item(CONTAINER_USERS, user_id, old_role)
            except Exception:
                pass
            dynamodb.create_item(CONTAINER_USERS, user.to_dict())
        else:
            dynamodb.update_item(CONTAINER_USERS, user_id, user.to_dict(), user.role)
        return user
    except Exception as e:
        logger.error(f'Error updating user: {e}')
        raise


def toggle_user_active(user_id: str) -> User:
    """Toggle user active status."""
    user = get_user_by_id(user_id)
    if user:
        user.is_active = not user.is_active
        user.updated_at = datetime.now(timezone.utc).isoformat()
        dynamodb.update_item(CONTAINER_USERS, user_id, user.to_dict(), user.role)
        return user
    return None


def get_all_users(page: int = 1, per_page: int = 25,
                  search: str = '', role_filter: str = '') -> tuple:
    """Get paginated user list with optional filters."""
    try:
        query = 'SELECT * FROM c WHERE 1=1'
        params = []
        if search:
            query += ' AND (CONTAINS(LOWER(c.email), @search) OR CONTAINS(LOWER(c.first_name), @search) OR CONTAINS(LOWER(c.last_name), @search))'
            params.append({'name': '@search', 'value': search.lower()})
        if role_filter:
            query += ' AND c.role = @role'
            params.append({'name': '@role', 'value': role_filter})
        query += ' ORDER BY c.created_at DESC'
        items, total = dynamodb.query_items_paged(CONTAINER_USERS, query, params, page, per_page)
        users = [User.from_dict(item) for item in items]
        return users, total
    except Exception as e:
        logger.error(f'Error getting users: {e}')
        return [], 0


def generate_jwt_token(user: User) -> str:
    """Generate a JWT token for API authentication."""
    payload = {
        'user_id': user.id,
        'email': user.email,
        'role': user.role,
        'exp': datetime.now(timezone.utc) + current_app.config.get('JWT_EXPIRATION_DELTA', timedelta(hours=24)),
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')


def verify_jwt_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def update_last_login(user_id: str, role: str = None):
    """Update user's last login timestamp."""
    try:
        if role is None:
            user = get_user_by_id(user_id)
            if user:
                role = user.role
            else:
                return
        items = dynamodb.query_items(
            CONTAINER_USERS,
            'SELECT * FROM c WHERE c.id = @id',
            [{'name': '@id', 'value': user_id}]
        )
        if items:
            items[0]['last_login'] = datetime.now(timezone.utc).isoformat()
            dynamodb.update_item(CONTAINER_USERS, user_id, items[0], items[0].get('role', role))
    except Exception as e:
        logger.error(f'Error updating last login: {e}')


def change_password(user_id: str, old_password: str, new_password: str) -> tuple:
    """Change user password. Returns (success, message)."""
    user = get_user_by_id(user_id)
    if not user:
        return False, 'User not found.'
    if not user.check_password(old_password):
        return False, 'Current password is incorrect.'
    user.set_password(new_password)
    user.updated_at = datetime.now(timezone.utc).isoformat()
    dynamodb.update_item(CONTAINER_USERS, user_id, user.to_dict(), user.role)
    return True, 'Password changed successfully.'


def create_default_admin():
    """Create default admin user if none exists."""
    try:
        admins = dynamodb.query_items(
            CONTAINER_USERS,
            'SELECT * FROM c WHERE c.role = @role',
            [{'name': '@role', 'value': 'admin'}],
            partition_key='admin'
        )
        if not admins:
            admin_data = {
                'email': current_app.config.get('ADMIN_EMAIL', 'admin@inventory.com'),
                'password': current_app.config.get('ADMIN_PASSWORD', 'Admin@123'),
                'first_name': current_app.config.get('ADMIN_FIRST_NAME', 'System'),
                'last_name': current_app.config.get('ADMIN_LAST_NAME', 'Administrator'),
                'role': 'admin',
                'is_active': True
            }
            create_user(admin_data)
            logger.info('Default admin user created.')
    except Exception as e:
        logger.warning(f'Could not create default admin (Cosmos DB may be unavailable): {e}')


def count_users() -> int:
    """Get total user count."""
    return dynamodb.count_items(CONTAINER_USERS)


def delete_user(user_id: str) -> bool:
    """Delete a user from Cosmos DB."""
    try:
        user = get_user_by_id(user_id)
        if user:
            dynamodb.delete_item(CONTAINER_USERS, user_id, user.role)
            logger.info(f'User deleted: {user.email}')
            return True
        return False
    except Exception as e:
        logger.error(f'Error deleting user: {e}')
        return False

