"""
Purchase Order model for Azure Cosmos DB.
"""

import uuid
from datetime import datetime, timezone


class PurchaseOrderItem:
    """Line item within a purchase order."""

    def __init__(self, **kwargs):
        self.product_id = kwargs.get('product_id', '')
        self.product_name = kwargs.get('product_name', '')
        self.sku = kwargs.get('sku', '')
        self.quantity = kwargs.get('quantity', 0)
        self.received_quantity = kwargs.get('received_quantity', 0)
        self.unit_price = kwargs.get('unit_price', 0.0)
        self.total = kwargs.get('total', 0.0)

    def calculate_total(self):
        self.total = round(self.quantity * self.unit_price, 2)
        return self.total

    def to_dict(self) -> dict:
        return {
            'product_id': self.product_id, 'product_name': self.product_name,
            'sku': self.sku, 'quantity': self.quantity,
            'received_quantity': self.received_quantity,
            'unit_price': self.unit_price, 'total': self.total
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)


class PurchaseOrder:
    """Purchase order document model."""

    STATUSES = ['draft', 'pending', 'approved', 'received', 'partial', 'cancelled']

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.order_number = kwargs.get('order_number', '')
        self.supplier_id = kwargs.get('supplier_id', '')
        self.supplier_name = kwargs.get('supplier_name', '')
        self.status = kwargs.get('status', 'draft')
        items_data = kwargs.get('items', [])
        self.items = []
        for item in items_data:
            if isinstance(item, PurchaseOrderItem):
                self.items.append(item)
            elif isinstance(item, dict):
                self.items.append(PurchaseOrderItem.from_dict(item))
        self.subtotal = kwargs.get('subtotal', 0.0)
        self.tax = kwargs.get('tax', 0.0)
        self.shipping = kwargs.get('shipping', 0.0)
        self.total_amount = kwargs.get('total_amount', 0.0)
        self.expected_delivery = kwargs.get('expected_delivery', '')
        self.warehouse_id = kwargs.get('warehouse_id', '')
        self.notes = kwargs.get('notes', '')
        self.created_by = kwargs.get('created_by', '')
        self.approved_by = kwargs.get('approved_by', '')
        self.created_at = kwargs.get('created_at', datetime.now(timezone.utc).isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.now(timezone.utc).isoformat())

    @staticmethod
    def generate_order_number(counter: int = 1) -> str:
        year = datetime.now(timezone.utc).strftime('%Y')
        return f"PO-{year}-{counter:05d}"

    def calculate_totals(self):
        self.subtotal = round(sum(item.total for item in self.items), 2)
        self.total_amount = round(self.subtotal + self.tax + self.shipping, 2)

    def can_approve(self) -> bool:
        return self.status in ('draft', 'pending')

    def can_receive(self) -> bool:
        return self.status in ('approved', 'partial')

    def can_cancel(self) -> bool:
        return self.status in ('draft', 'pending', 'approved')

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'order_number': self.order_number,
            'supplier_id': self.supplier_id, 'supplier_name': self.supplier_name,
            'status': self.status,
            'items': [item.to_dict() for item in self.items],
            'subtotal': self.subtotal, 'tax': self.tax,
            'shipping': self.shipping, 'total_amount': self.total_amount,
            'expected_delivery': self.expected_delivery,
            'warehouse_id': self.warehouse_id, 'notes': self.notes,
            'created_by': self.created_by, 'approved_by': self.approved_by,
            'created_at': self.created_at, 'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)
