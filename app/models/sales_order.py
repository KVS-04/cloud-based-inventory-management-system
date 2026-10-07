"""
Sales Order model for Azure Cosmos DB.
"""

import uuid
from datetime import datetime, timezone


class SalesOrderItem:
    """Line item within a sales order."""

    def __init__(self, **kwargs):
        self.product_id = kwargs.get('product_id', '')
        self.product_name = kwargs.get('product_name', '')
        self.sku = kwargs.get('sku', '')
        self.quantity = kwargs.get('quantity', 0)
        self.unit_price = kwargs.get('unit_price', 0.0)
        self.discount = kwargs.get('discount', 0.0)
        self.total = kwargs.get('total', 0.0)

    def calculate_total(self):
        self.total = round((self.quantity * self.unit_price) - self.discount, 2)
        return self.total

    def to_dict(self) -> dict:
        return {
            'product_id': self.product_id, 'product_name': self.product_name,
            'sku': self.sku, 'quantity': self.quantity,
            'unit_price': self.unit_price, 'discount': self.discount,
            'total': self.total
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)


class SalesOrder:
    """Sales order document model."""

    STATUSES = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
    CHANNELS = ['pos', 'ecommerce', 'warehouse', 'manual']
    PAYMENT_STATUSES = ['pending', 'paid', 'refunded']

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.order_number = kwargs.get('order_number', '')
        self.customer_name = kwargs.get('customer_name', '')
        self.customer_email = kwargs.get('customer_email', '')
        self.customer_phone = kwargs.get('customer_phone', '')
        self.channel = kwargs.get('channel', 'manual')
        self.status = kwargs.get('status', 'pending')
        items_data = kwargs.get('items', [])
        self.items = []
        for item in items_data:
            if isinstance(item, SalesOrderItem):
                self.items.append(item)
            elif isinstance(item, dict):
                self.items.append(SalesOrderItem.from_dict(item))
        self.subtotal = kwargs.get('subtotal', 0.0)
        self.tax = kwargs.get('tax', 0.0)
        self.discount = kwargs.get('discount', 0.0)
        self.total_amount = kwargs.get('total_amount', 0.0)
        self.payment_status = kwargs.get('payment_status', 'pending')
        self.shipping_address = kwargs.get('shipping_address', '')
        self.notes = kwargs.get('notes', '')
        self.created_by = kwargs.get('created_by', '')
        self.created_at = kwargs.get('created_at', datetime.now(timezone.utc).isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.now(timezone.utc).isoformat())

    @staticmethod
    def generate_order_number(counter: int = 1) -> str:
        year = datetime.now(timezone.utc).strftime('%Y')
        return f"SO-{year}-{counter:05d}"

    def calculate_totals(self):
        self.subtotal = round(sum(item.total for item in self.items), 2)
        self.total_amount = round(self.subtotal + self.tax - self.discount, 2)

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'order_number': self.order_number,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'channel': self.channel, 'status': self.status,
            'items': [item.to_dict() for item in self.items],
            'subtotal': self.subtotal, 'tax': self.tax,
            'discount': self.discount, 'total_amount': self.total_amount,
            'payment_status': self.payment_status,
            'shipping_address': self.shipping_address,
            'notes': self.notes, 'created_by': self.created_by,
            'created_at': self.created_at, 'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)
