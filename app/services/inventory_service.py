"""
Inventory service - Stock management, movements, adjustments.
"""

import logging
from datetime import datetime, timezone

from ..models.inventory import InventoryItem
from ..models.movement import InventoryMovement
from ..services.dynamodb_service import dynamodb
from ..services.sqs_service import sqs_service
from ..utils.constants import CONTAINER_INVENTORY, CONTAINER_MOVEMENTS

logger = logging.getLogger(__name__)


def get_all_inventory(page=1, per_page=25, warehouse_id='', category='',
                      stock_status='', search='', sort_by='last_updated', sort_order='DESC'):
    try:
        query = 'SELECT * FROM c WHERE 1=1'
        params = []
        if warehouse_id:
            query += ' AND c.warehouse_id = @wid'
            params.append({'name': '@wid', 'value': warehouse_id})
        if search:
            query += ' AND (CONTAINS(LOWER(c.product_name), @search) OR CONTAINS(LOWER(c.sku), @search))'
            params.append({'name': '@search', 'value': search.lower()})
        query += f' ORDER BY c.last_updated DESC'
        items, total = dynamodb.query_items_paged(CONTAINER_INVENTORY, query, params, page, per_page)
        inventory = [InventoryItem.from_dict(item) for item in items]
        return inventory, total
    except Exception as e:
        logger.error(f'Error getting inventory: {e}')
        return [], 0


def get_inventory_by_product(product_id):
    items = dynamodb.query_items(CONTAINER_INVENTORY,
                                  'SELECT * FROM c WHERE c.product_id = @pid',
                                  [{'name': '@pid', 'value': product_id}])
    return [InventoryItem.from_dict(item) for item in items]


def get_inventory_item(inventory_id):
    items = dynamodb.query_items(CONTAINER_INVENTORY,
                                  'SELECT * FROM c WHERE c.id = @id',
                                  [{'name': '@id', 'value': inventory_id}])
    return InventoryItem.from_dict(items[0]) if items else None


def adjust_stock(product_id, warehouse_id, quantity_change, movement_type,
                 reason='', user_id='', user_name='', reference_type='manual',
                 reference_id='', product_name=''):
    """Adjust stock quantity and create a movement record."""
    try:
        # Find or create inventory record
        items = dynamodb.query_items(
            CONTAINER_INVENTORY,
            'SELECT * FROM c WHERE c.product_id = @pid AND c.warehouse_id = @wid',
            [{'name': '@pid', 'value': product_id},
             {'name': '@wid', 'value': warehouse_id}]
        )
        if items:
            inv = InventoryItem.from_dict(items[0])
        else:
            from ..services.product_service import get_product
            from ..services.order_service import get_warehouse
            prod = get_product(product_id)
            wh = get_warehouse(warehouse_id)
            p_name = prod.name if prod else product_name
            sku = prod.sku if prod else ''
            w_name = wh.name if wh else ''
            inv = InventoryItem(
                product_id=product_id, product_name=p_name, sku=sku,
                warehouse_id=warehouse_id, warehouse_name=w_name, quantity=0
            )
        previous_qty = inv.quantity
        if movement_type in ('stock_in', 'return'):
            inv.quantity += abs(quantity_change)
        elif movement_type == 'stock_out':
            inv.quantity = max(0, inv.quantity - abs(quantity_change))
        elif movement_type == 'adjustment':
            inv.quantity = max(0, inv.quantity + quantity_change)
        else:
            inv.quantity = max(0, inv.quantity + quantity_change)

        inv.update_available_quantity()
        inv.last_updated = datetime.now(timezone.utc).isoformat()

        # Create movement record
        movement = InventoryMovement(
            product_id=product_id, product_name=product_name or inv.product_name,
            warehouse_id=warehouse_id, movement_type=movement_type,
            quantity=abs(quantity_change), previous_quantity=previous_qty,
            new_quantity=inv.quantity, reference_type=reference_type,
            reference_id=reference_id, reason=reason,
            performed_by=user_id, performed_by_name=user_name
        )
        # Save inventory
        if items:
            dynamodb.update_item(CONTAINER_INVENTORY, inv.id, inv.to_dict(), warehouse_id)
        else:
            dynamodb.create_item(CONTAINER_INVENTORY, inv.to_dict())
        # Save movement
        dynamodb.create_item(CONTAINER_MOVEMENTS, movement.to_dict())
        # Send queue message
        sqs_service.send_inventory_update(
            product_id, warehouse_id, quantity_change, movement_type, reference_id, user_id
        )
        logger.info(f'Stock adjusted: {product_id} {movement_type} {quantity_change}')
        return inv, movement
    except Exception as e:
        logger.error(f'Error adjusting stock: {e}')
        raise


def transfer_stock(product_id, source_warehouse, dest_warehouse,
                   quantity, user_id='', user_name='', product_name=''):
    """Transfer stock between warehouses."""
    # Deduct from source
    adjust_stock(product_id, source_warehouse, -quantity, 'stock_out',
                 reason=f'Transfer to {dest_warehouse}', user_id=user_id,
                 user_name=user_name, reference_type='manual', product_name=product_name)
    # Add to destination
    adjust_stock(product_id, dest_warehouse, quantity, 'stock_in',
                 reason=f'Transfer from {source_warehouse}', user_id=user_id,
                 user_name=user_name, reference_type='manual', product_name=product_name)


def get_movement_history(product_id='', warehouse_id='', movement_type='',
                         date_from='', date_to='', page=1, per_page=25):
    query = 'SELECT * FROM c WHERE 1=1'
    params = []
    if product_id:
        query += ' AND c.product_id = @pid'
        params.append({'name': '@pid', 'value': product_id})
    if warehouse_id:
        query += ' AND c.warehouse_id = @wid'
        params.append({'name': '@wid', 'value': warehouse_id})
    if movement_type:
        query += ' AND c.movement_type = @mt'
        params.append({'name': '@mt', 'value': movement_type})
    if date_from:
        query += ' AND c.created_at >= @df'
        params.append({'name': '@df', 'value': date_from})
    if date_to:
        query += ' AND c.created_at <= @dt'
        params.append({'name': '@dt', 'value': date_to})
    query += ' ORDER BY c.created_at DESC'
    items, total = dynamodb.query_items_paged(CONTAINER_MOVEMENTS, query, params, page, per_page)
    movements = [InventoryMovement.from_dict(item) for item in items]
    return movements, total


def get_low_stock_items():
    """Get inventory items below their product's reorder point."""
    items = dynamodb.query_items(CONTAINER_INVENTORY, 'SELECT * FROM c WHERE c.quantity <= 20')
    return [InventoryItem.from_dict(item) for item in items]


def get_inventory_value():
    """Calculate total inventory value."""
    items = dynamodb.query_items(CONTAINER_INVENTORY, 'SELECT c.quantity FROM c')
    return sum(item.get('quantity', 0) for item in items)


def get_stock_summary():
    """Get stock statistics."""
    items = dynamodb.query_items(CONTAINER_INVENTORY, 'SELECT * FROM c')
    total_items = len(items)
    total_value = sum(i.get('quantity', 0) for i in items)
    low_stock = sum(1 for i in items if i.get('quantity', 0) <= 20)
    out_of_stock = sum(1 for i in items if i.get('quantity', 0) <= 0)
    return {
        'total_items': total_items, 'total_quantity': total_value,
        'low_stock_count': low_stock, 'out_of_stock_count': out_of_stock
    }


def initialize_inventory(product_id, warehouse_id, quantity, location='',
                          product_name='', sku='', warehouse_name=''):
    """Create initial inventory record for a product in a warehouse."""
    inv = InventoryItem(
        product_id=product_id, product_name=product_name, sku=sku,
        warehouse_id=warehouse_id, warehouse_name=warehouse_name,
        quantity=quantity, available_quantity=quantity, location=location
    )
    dynamodb.create_item(CONTAINER_INVENTORY, inv.to_dict())
    return inv


def count_inventory_items():
    return dynamodb.count_items(CONTAINER_INVENTORY)
