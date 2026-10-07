"""
Warehouse model for Azure Cosmos DB.
"""

import uuid
from datetime import datetime, timezone


class Warehouse:
    """Warehouse document model."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.name = kwargs.get('name', '')
        self.code = kwargs.get('code', '')
        self.region = kwargs.get('region', '')
        self.address = kwargs.get('address', {
            'street': '', 'city': '', 'state': '', 'zip': '', 'country': ''
        })
        self.manager_id = kwargs.get('manager_id', '')
        self.capacity = kwargs.get('capacity', 10000)
        self.is_active = kwargs.get('is_active', True)
        self.created_at = kwargs.get('created_at', datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'name': self.name, 'code': self.code,
            'region': self.region, 'address': self.address,
            'manager_id': self.manager_id, 'capacity': self.capacity,
            'is_active': self.is_active, 'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)
