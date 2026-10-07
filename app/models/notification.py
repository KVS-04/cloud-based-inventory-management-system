"""
Notification model for Azure Cosmos DB.
"""

import uuid
from datetime import datetime, timezone


class Notification:
    """Notification document model."""

    TYPES = ['low_stock', 'reorder', 'order_update', 'system', 'alert']
    SEVERITIES = ['info', 'warning', 'critical']

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id', '')
        self.type = kwargs.get('type', 'system')
        self.title = kwargs.get('title', '')
        self.message = kwargs.get('message', '')
        self.severity = kwargs.get('severity', 'info')
        self.is_read = kwargs.get('is_read', False)
        self.action_url = kwargs.get('action_url', '')
        self.created_at = kwargs.get('created_at', datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'user_id': self.user_id, 'type': self.type,
            'title': self.title, 'message': self.message,
            'severity': self.severity, 'is_read': self.is_read,
            'action_url': self.action_url, 'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)
