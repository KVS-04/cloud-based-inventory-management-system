"""
Audit Log model for Azure Cosmos DB.
"""

import uuid
from datetime import datetime, timezone


class AuditLog:
    """Audit log document for tracking all system changes."""

    ACTIONS = ['create', 'update', 'delete', 'login', 'logout', 'export', 'approve', 'receive', 'cancel']

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id', '')
        self.user_name = kwargs.get('user_name', '')
        self.action = kwargs.get('action', '')
        self.entity_type = kwargs.get('entity_type', '')
        self.entity_id = kwargs.get('entity_id', '')
        self.changes = kwargs.get('changes', {})
        self.ip_address = kwargs.get('ip_address', '')
        self.user_agent = kwargs.get('user_agent', '')
        self.timestamp = kwargs.get('timestamp', datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'user_id': self.user_id,
            'user_name': self.user_name, 'action': self.action,
            'entity_type': self.entity_type, 'entity_id': self.entity_id,
            'changes': self.changes, 'ip_address': self.ip_address,
            'user_agent': self.user_agent, 'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)

    @classmethod
    def create_log(cls, user, action: str, entity_type: str,
                   entity_id: str, changes: dict = None, request=None):
        """Factory method to create an audit log entry."""
        return cls(
            user_id=user.id if user else '',
            user_name=user.full_name if user else 'System',
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes or {},
            ip_address=request.remote_addr if request else '',
            user_agent=request.user_agent.string if request else ''
        )
