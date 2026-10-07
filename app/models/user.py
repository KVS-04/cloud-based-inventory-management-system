"""
User model for Azure Cosmos DB.
Implements Flask-Login UserMixin for session-based authentication.
"""

import uuid
from datetime import datetime, timezone
import bcrypt
from flask_login import UserMixin


class User(UserMixin):
    """User document model for Cosmos DB users container."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.username = kwargs.get('username', '')
        self.email = kwargs.get('email', '')
        self.password_hash = kwargs.get('password_hash', '')
        self.role = kwargs.get('role', 'staff')  # admin, manager, staff
        self.first_name = kwargs.get('first_name', '')
        self.last_name = kwargs.get('last_name', '')
        self.phone = kwargs.get('phone', '')
        self.avatar_url = kwargs.get('avatar_url', '')
        self._is_active = kwargs.get('is_active', True)
        self.last_login = kwargs.get('last_login', '')
        self.created_at = kwargs.get('created_at', datetime.now(timezone.utc).isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.now(timezone.utc).isoformat())

    # --- Flask-Login required properties ---
    def get_id(self):
        return self.id

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

    @property
    def active(self):
        return self._is_active

    # --- Password management ---
    def set_password(self, password: str):
        """Hash and set the user's password using bcrypt."""
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    # --- Role checks ---
    def is_admin(self) -> bool:
        return self.role == 'admin'

    def is_manager(self) -> bool:
        return self.role == 'manager'

    def is_staff(self) -> bool:
        return self.role == 'staff'

    def has_role(self, *roles) -> bool:
        return self.role in roles

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    # --- Serialization ---
    def to_dict(self) -> dict:
        """Convert user to Cosmos DB document dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'role': self.role,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'last_login': self.last_login,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def to_safe_dict(self) -> dict:
        """Convert to dict without sensitive data (no password_hash)."""
        data = self.to_dict()
        data.pop('password_hash', None)
        return data

    @classmethod
    def from_dict(cls, data: dict):
        """Create a User instance from a Cosmos DB document."""
        if not data:
            return None
        return cls(**data)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
