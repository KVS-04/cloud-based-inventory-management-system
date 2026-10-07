"""
Inventory movement model for Azure Cosmos DB.
Tracks all stock changes with full audit trail.
"""

import uuid
from datetime import datetime, timezone


class InventoryMovement:
    """Inventory movement document for tracking stock changes."""

    MOVEMENT_TYPES = ['stock_in', 'stock_out', 'transfer', 'adjustment', 'return']
    REFERENCE_TYPES = ['purchase_order', 'sales_order', 'return', 'manual', 'system']

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.product_id = kwargs.get('product_id', '')
        self.product_name = kwargs.get('product_name', '')
        self.warehouse_id = kwargs.get('warehouse_id', '')
        self.movement_type = kwargs.get('movement_type', 'adjustment')
        self.quantity = kwargs.get('quantity', 0)
        self.previous_quantity = kwargs.get('previous_quantity', 0)
        self.new_quantity = kwargs.get('new_quantity', 0)
        self.reference_type = kwargs.get('reference_type', 'manual')
        self.reference_id = kwargs.get('reference_id', '')
        self.reason = kwargs.get('reason', '')
        self.notes = kwargs.get('notes', '')
        self.performed_by = kwargs.get('performed_by', '')
        self.performed_by_name = kwargs.get('performed_by_name', '')
        self.created_at = kwargs.get('created_at', datetime.now(timezone.utc).isoformat())

    @property
    def is_inbound(self) -> bool:
        return self.movement_type in ('stock_in', 'return')

    @property
    def is_outbound(self) -> bool:
        return self.movement_type == 'stock_out'

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'product_id': self.product_id,
            'product_name': self.product_name, 'warehouse_id': self.warehouse_id,
            'movement_type': self.movement_type, 'quantity': self.quantity,
            'previous_quantity': self.previous_quantity,
            'new_quantity': self.new_quantity,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id, 'reason': self.reason,
            'notes': self.notes, 'performed_by': self.performed_by,
            'performed_by_name': self.performed_by_name,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)
