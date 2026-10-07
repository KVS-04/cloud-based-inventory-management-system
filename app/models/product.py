"""
Product model for Azure Cosmos DB.
"""

import uuid
import random
import string
from datetime import datetime, timezone


class Product:
    """Product document model for Cosmos DB products container."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.sku = kwargs.get('sku', '')
        self.name = kwargs.get('name', '')
        self.description = kwargs.get('description', '')
        self.category = kwargs.get('category', '')
        self.subcategory = kwargs.get('subcategory', '')
        self.barcode = kwargs.get('barcode', '')
        self.barcode_image_url = kwargs.get('barcode_image_url', '')
        self.price = kwargs.get('price', 0.0)
        self.cost_price = kwargs.get('cost_price', 0.0)
        self.unit = kwargs.get('unit', 'pcs')
        self.weight = kwargs.get('weight', 0.0)
        self.dimensions = kwargs.get('dimensions', {'length': 0, 'width': 0, 'height': 0})
        self.image_url = kwargs.get('image_url', '')
        self.min_stock_level = kwargs.get('min_stock_level', 10)
        self.reorder_point = kwargs.get('reorder_point', 20)
        self.reorder_quantity = kwargs.get('reorder_quantity', 50)
        self.max_stock_level = kwargs.get('max_stock_level', 500)
        self.supplier_id = kwargs.get('supplier_id', '')
        self.tags = kwargs.get('tags', [])
        self.is_active = kwargs.get('is_active', True)
        self.created_at = kwargs.get('created_at', datetime.now(timezone.utc).isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.now(timezone.utc).isoformat())

    def generate_sku(self) -> str:
        """Generate a unique SKU based on category prefix and random suffix."""
        prefix = ''.join(c for c in self.category[:3].upper() if c.isalpha()) or 'PRD'
        timestamp = datetime.now(timezone.utc).strftime('%y%m')
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        self.sku = f"{prefix}-{timestamp}-{suffix}"
        return self.sku

    @property
    def profit_margin(self) -> float:
        """Calculate profit margin percentage."""
        if self.cost_price and self.cost_price > 0:
            return ((self.price - self.cost_price) / self.cost_price) * 100
        return 0.0

    def validate(self) -> tuple:
        """Validate product data. Returns (is_valid, errors)."""
        errors = []
        if not self.name:
            errors.append('Product name is required.')
        if not self.category:
            errors.append('Category is required.')
        if self.price < 0:
            errors.append('Price cannot be negative.')
        if self.cost_price < 0:
            errors.append('Cost price cannot be negative.')
        if self.min_stock_level < 0:
            errors.append('Minimum stock level cannot be negative.')
        if self.reorder_point < 0:
            errors.append('Reorder point cannot be negative.')
        return (len(errors) == 0, errors)

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'sku': self.sku, 'name': self.name,
            'description': self.description, 'category': self.category,
            'subcategory': self.subcategory, 'barcode': self.barcode,
            'barcode_image_url': self.barcode_image_url,
            'price': self.price, 'cost_price': self.cost_price,
            'unit': self.unit, 'weight': self.weight,
            'dimensions': self.dimensions, 'image_url': self.image_url,
            'min_stock_level': self.min_stock_level,
            'reorder_point': self.reorder_point,
            'reorder_quantity': self.reorder_quantity,
            'max_stock_level': self.max_stock_level,
            'supplier_id': self.supplier_id, 'tags': self.tags,
            'is_active': self.is_active,
            'created_at': self.created_at, 'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)

    def __repr__(self):
        return f"<Product {self.sku}: {self.name}>"
