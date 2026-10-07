"""
Supplier model for Azure Cosmos DB.
"""

import uuid
from datetime import datetime, timezone


class Supplier:
    """Supplier document model."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.name = kwargs.get('name', '')
        self.code = kwargs.get('code', '')
        self.contact_person = kwargs.get('contact_person', '')
        self.email = kwargs.get('email', '')
        self.phone = kwargs.get('phone', '')
        self.address = kwargs.get('address', {
            'street': '', 'city': '', 'state': '', 'zip': '', 'country': ''
        })
        self.category = kwargs.get('category', '')
        self.payment_terms = kwargs.get('payment_terms', 'Net 30')
        self.lead_time_days = kwargs.get('lead_time_days', 7)
        self.rating = kwargs.get('rating', 0.0)
        self.is_active = kwargs.get('is_active', True)
        self.notes = kwargs.get('notes', '')
        self.created_at = kwargs.get('created_at', datetime.now(timezone.utc).isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.now(timezone.utc).isoformat())

    @staticmethod
    def generate_code(counter: int = 1) -> str:
        return f"SUP-{counter:03d}"

    @property
    def full_address(self) -> str:
        parts = [
            self.address.get('street', ''),
            self.address.get('city', ''),
            self.address.get('state', ''),
            self.address.get('zip', ''),
            self.address.get('country', '')
        ]
        return ', '.join(p for p in parts if p)

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'name': self.name, 'code': self.code,
            'contact_person': self.contact_person, 'email': self.email,
            'phone': self.phone, 'address': self.address,
            'category': self.category, 'payment_terms': self.payment_terms,
            'lead_time_days': self.lead_time_days, 'rating': self.rating,
            'is_active': self.is_active, 'notes': self.notes,
            'created_at': self.created_at, 'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)
