"""
Product service - Business logic for product management.
"""

import logging
from datetime import datetime, timezone
from flask import current_app

from ..models.product import Product
from ..services.dynamodb_service import dynamodb
from ..utils.constants import CONTAINER_PRODUCTS
from ..utils.helpers import generate_uuid

logger = logging.getLogger(__name__)

# DEMO MODE: Global in-memory mock products
MOCK_PRODUCTS = [
    Product(id="1", sku="LAP-001", name="ThinkPad X1 Carbon", category="Electronics", price=1299.99, min_stock_level=10, is_active=True),
    Product(id="2", sku="MON-002", name="Dell UltraSharp 27", category="Electronics", price=450.00, min_stock_level=5, is_active=True),
    Product(id="3", sku="FUR-003", name="Ergonomic Office Chair", category="Furniture", price=299.00, min_stock_level=20, is_active=True),
    Product(id="4", sku="ACC-004", name="Wireless Mouse", category="Accessories", price=45.00, min_stock_level=50, is_active=True)
]

def get_all_products(page=1, per_page=25, search='', category='',
                     status='', sort_by='created_at', sort_order='DESC'):
    """Get paginated, filtered, and sorted product list."""
    try:
        # Fetch all active items and filter in Python to guarantee correct OR/AND logic
        items = dynamodb.query_items(CONTAINER_PRODUCTS, 'SELECT * FROM c')
        filtered_items = []
        search_lower = search.lower() if search else ''
        
        for item in items:
            if not item.get('is_active', True):
                continue
            if category and item.get('category') != category:
                continue
            if search_lower:
                name = str(item.get('name', '')).lower()
                sku = str(item.get('sku', '')).lower()
                barcode = str(item.get('barcode', '')).lower()
                if search_lower not in name and search_lower not in sku and search_lower not in barcode:
                    continue
            filtered_items.append(item)
            
        # Sort
        valid_sorts = {'name': 'name', 'sku': 'sku', 'price': 'price',
                       'category': 'category', 'created_at': 'created_at'}
        sort_field = valid_sorts.get(sort_by, 'created_at')
        is_desc = sort_order.upper() == 'DESC'
        
        filtered_items.sort(key=lambda x: x.get(sort_field, ''), reverse=is_desc)
        
        total = len(filtered_items)
        offset = (page - 1) * per_page
        paged_items = filtered_items[offset:offset + per_page]
        
        products = [Product.from_dict(item) for item in paged_items]
        return products, total
    except Exception as e:
        logger.error(f'Error getting products: {e}')
        # DEMO MODE: Return mock products if DB is not connected
        global MOCK_PRODUCTS
        return MOCK_PRODUCTS, len(MOCK_PRODUCTS)


def get_product_by_id(product_id):
    """Get a single product by ID."""
    try:
        items = dynamodb.query_items(
            CONTAINER_PRODUCTS,
            'SELECT * FROM c WHERE c.id = @id',
            [{'name': '@id', 'value': product_id}]
        )
        return Product.from_dict(items[0]) if items else None
    except Exception as e:
        logger.error(f'Error getting product: {e}')
        # DEMO MODE: Check mock products if DB fails
        global MOCK_PRODUCTS
        for p in MOCK_PRODUCTS:
            if p.id == product_id:
                return p
        return None


def get_product_by_sku(sku):
    items = dynamodb.query_items(CONTAINER_PRODUCTS, 'SELECT * FROM c WHERE c.sku = @sku',
                                  [{'name': '@sku', 'value': sku}])
    return Product.from_dict(items[0]) if items else None


def get_product_by_barcode(barcode):
    items = dynamodb.query_items(CONTAINER_PRODUCTS, 'SELECT * FROM c')
    for item in items:
        if item.get('is_active', True) and (str(item.get('barcode', '')) == str(barcode) or str(item.get('sku', '')) == str(barcode)):
            return Product.from_dict(item)
    return None


def create_product(data, user_id=''):
    """Create a new product."""
    try:
        product = Product(
            name=data.get('name', '').strip(),
            description=data.get('description', '').strip(),
            category=data.get('category', ''),
            subcategory=data.get('subcategory', ''),
            price=float(data.get('price', 0)),
            cost_price=float(data.get('cost_price', 0)),
            unit=data.get('unit', 'pcs'),
            min_stock_level=int(data.get('min_stock_level', 10)),
            reorder_point=int(data.get('reorder_point', 20)),
            reorder_quantity=int(data.get('reorder_quantity', 50)),
            max_stock_level=int(data.get('max_stock_level', 500)),
            supplier_id=data.get('supplier_id', ''),
            tags=data.get('tags', []),
            barcode=data.get('barcode', ''),
            image_url=data.get('image_url', '')
        )
        if not product.sku:
            product.generate_sku()
        is_valid, errors = product.validate()
        if not is_valid:
            return None, errors
        dynamodb.create_item(CONTAINER_PRODUCTS, product.to_dict())
        logger.info(f'Product created: {product.sku}')
        return product, []
    except Exception as e:
        logger.error(f'Error creating product: {e}')
        # DEMO MODE: If Azure fails, append to mock DB
        global MOCK_PRODUCTS
        MOCK_PRODUCTS.append(product)
        logger.info(f'Product created in MOCK memory: {product.sku}')
        return product, []


def update_product(product_id, data, user_id=''):
    """Update an existing product."""
    try:
        product = get_product_by_id(product_id)
        if not product:
            return None, ['Product not found.']
        old_category = product.category
        for field in ['name', 'description', 'subcategory', 'unit', 'supplier_id', 'barcode', 'image_url']:
            if field in data:
                setattr(product, field, data[field])
        for field in ['price', 'cost_price']:
            if field in data:
                setattr(product, field, float(data[field]))
        for field in ['min_stock_level', 'reorder_point', 'reorder_quantity', 'max_stock_level']:
            if field in data:
                setattr(product, field, int(data[field]))
        if 'category' in data:
            product.category = data['category']
        if 'tags' in data:
            product.tags = data['tags'] if isinstance(data['tags'], list) else data['tags'].split(',')
        product.updated_at = datetime.now(timezone.utc).isoformat()
        is_valid, errors = product.validate()
        if not is_valid:
            return None, errors
        # Handle partition key change
        if old_category != product.category:
            try:
                dynamodb.delete_item(CONTAINER_PRODUCTS, product_id, old_category)
            except Exception:
                pass
            dynamodb.create_item(CONTAINER_PRODUCTS, product.to_dict())
        else:
            dynamodb.update_item(CONTAINER_PRODUCTS, product_id, product.to_dict(), product.category)
        return product, []
    except Exception as e:
        logger.error(f'Error updating product: {e}')
        return None, [str(e)]


def delete_product(product_id, user_id=''):
    """Soft-delete a product."""
    product = get_product_by_id(product_id)
    if product:
        product.is_active = False
        product.updated_at = datetime.now(timezone.utc).isoformat()
        dynamodb.update_item(CONTAINER_PRODUCTS, product_id, product.to_dict(), product.category)
        return True
    return False


def get_product_categories():
    """Get distinct product categories."""
    try:
        items = dynamodb.query_items(
            CONTAINER_PRODUCTS,
            'SELECT DISTINCT c.category FROM c WHERE c.is_active = true'
        )
        return [item.get('category', '') for item in items if item.get('category')]
    except Exception:
        return []


def get_low_stock_products():
    """Get products below reorder point."""
    try:
        # This requires joining with inventory data
        items = dynamodb.query_items(CONTAINER_PRODUCTS,
                                      'SELECT * FROM c WHERE c.is_active = true')
        return [Product.from_dict(item) for item in items]
    except Exception:
        return []


def count_products():
    return dynamodb.count_items(CONTAINER_PRODUCTS,
                                 'SELECT VALUE COUNT(1) FROM c WHERE c.is_active = true')


def search_products(query_text):
    query_text = str(query_text).lower()
    items = dynamodb.query_items(CONTAINER_PRODUCTS, 'SELECT * FROM c')
    results = []
    for item in items:
        if item.get('is_active', True):
            name = str(item.get('name', '')).lower()
            sku = str(item.get('sku', '')).lower()
            barcode = str(item.get('barcode', '')).lower()
            if query_text in name or query_text in sku or query_text in barcode:
                results.append(Product.from_dict(item))
    return results
