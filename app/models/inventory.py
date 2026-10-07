"""
Inventory item model for Azure Cosmos DB.
"""

import uuid
from datetime import datetime, timezone


class InventoryItem:
    """Inventory document model for Cosmos DB inventory container."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.product_id = kwargs.get('product_id', '')
        self.product_name = kwargs.get('product_name', '')
        self.sku = kwargs.get('sku', '')
        self.warehouse_id = kwargs.get('warehouse_id', '')
        self.warehouse_name = kwargs.get('warehouse_name', '')
        self.quantity = kwargs.get('quantity', 0)
        self.reserved_quantity = kwargs.get('reserved_quantity', 0)
        self.available_quantity = kwargs.get('available_quantity', 0)
        self.location = kwargs.get('location', '')
        self.batch_number = kwargs.get('batch_number', '')
        self.expiry_date = kwargs.get('expiry_date', None)
        self.last_counted = kwargs.get('last_counted', '')
        self.last_updated = kwargs.get('last_updated', datetime.now(timezone.utc).isoformat())

    def update_available_quantity(self):
        """Recalculate available quantity."""
        self.available_quantity = max(0, self.quantity - self.reserved_quantity)

    def is_low_stock(self, reorder_point: int) -> bool:
        """Check if stock is below reorder point."""
        return self.available_quantity <= reorder_point

    def is_out_of_stock(self) -> bool:
        return self.available_quantity <= 0

    def is_expired(self) -> bool:
        """Check if the batch has expired."""
        if not self.expiry_date:
            return False
        try:
            exp = datetime.fromisoformat(self.expiry_date.replace('Z', '+00:00'))
            return datetime.now(timezone.utc) > exp
        except (ValueError, AttributeError):
            return False

    def get_stock_status(self, reorder_point: int = 20, min_stock: int = 10) -> str:
        """Return stock status: critical, low, normal, overstocked."""
        if self.available_quantity <= 0:
            return 'out_of_stock'
        elif self.available_quantity <= min_stock:
            return 'critical'
        elif self.available_quantity <= reorder_point:
            return 'low'
        else:
            return 'normal'

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'product_id': self.product_id,
            'product_name': self.product_name, 'sku': self.sku,
            'warehouse_id': self.warehouse_id, 'warehouse_name': self.warehouse_name,
            'quantity': self.quantity, 'reserved_quantity': self.reserved_quantity,
            'available_quantity': self.available_quantity,
            'location': self.location, 'batch_number': self.batch_number,
            'expiry_date': self.expiry_date, 'last_counted': self.last_counted,
            'last_updated': self.last_updated
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)

    def __repr__(self):
        return f"<InventoryItem {self.sku} @ {self.warehouse_name}: {self.available_quantity}>"
