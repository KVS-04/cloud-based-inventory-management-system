"""
Return model for Azure Cosmos DB.
"""

import uuid
from datetime import datetime, timezone


class ReturnItem:
    """Line item within a return."""

    def __init__(self, **kwargs):
        self.product_id = kwargs.get('product_id', '')
        self.product_name = kwargs.get('product_name', '')
        self.quantity = kwargs.get('quantity', 0)
        self.reason = kwargs.get('reason', '')  # defective, wrong_item, damaged, not_needed
        self.condition = kwargs.get('condition', 'new')  # new, used, damaged

    def to_dict(self) -> dict:
        return {
            'product_id': self.product_id, 'product_name': self.product_name,
            'quantity': self.quantity, 'reason': self.reason,
            'condition': self.condition
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)


class Return:
    """Return document model."""

    STATUSES = ['pending', 'approved', 'received', 'processed', 'rejected']
    TYPES = ['customer', 'supplier']
    REASONS = ['defective', 'wrong_item', 'damaged', 'not_needed', 'expired', 'other']

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.return_number = kwargs.get('return_number', '')
        self.return_type = kwargs.get('return_type', 'customer')
        self.order_id = kwargs.get('order_id', '')
        self.order_number = kwargs.get('order_number', '')
        self.status = kwargs.get('status', 'pending')
        items_data = kwargs.get('items', [])
        self.items = []
        for item in items_data:
            if isinstance(item, ReturnItem):
                self.items.append(item)
            elif isinstance(item, dict):
                self.items.append(ReturnItem.from_dict(item))
        self.total_refund = kwargs.get('total_refund', 0.0)
        self.notes = kwargs.get('notes', '')
        self.processed_by = kwargs.get('processed_by', '')
        self.created_by = kwargs.get('created_by', '')
        self.created_at = kwargs.get('created_at', datetime.now(timezone.utc).isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.now(timezone.utc).isoformat())

    @staticmethod
    def generate_return_number(counter: int = 1) -> str:
        year = datetime.now(timezone.utc).strftime('%Y')
        return f"RET-{year}-{counter:05d}"

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'return_number': self.return_number,
            'return_type': self.return_type, 'order_id': self.order_id,
            'order_number': self.order_number, 'status': self.status,
            'items': [item.to_dict() for item in self.items],
            'total_refund': self.total_refund, 'notes': self.notes,
            'processed_by': self.processed_by, 'created_by': self.created_by,
            'created_at': self.created_at, 'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)
