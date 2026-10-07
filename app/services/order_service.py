"""
Purchase Order service, Sales Order service, Returns service,
Supplier service, Warehouse service - combined for efficiency.
"""

import logging
from datetime import datetime, timezone

from ..models.purchase_order import PurchaseOrder
from ..models.sales_order import SalesOrder
from ..models.returns import Return
from ..models.supplier import Supplier
from ..models.warehouse import Warehouse
from ..services.dynamodb_service import dynamodb
from ..utils.constants import (CONTAINER_PURCHASE_ORDERS, CONTAINER_SALES_ORDERS,
                                CONTAINER_RETURNS, CONTAINER_SUPPLIERS, CONTAINER_WAREHOUSES)

logger = logging.getLogger(__name__)


# ==================== PURCHASE ORDERS ====================

def get_all_purchase_orders(page=1, per_page=25, status='', supplier_id='',
                             search='', sort_by='created_at', sort_order='DESC'):
    query = 'SELECT * FROM c WHERE 1=1'
    params = []
    if status:
        query += ' AND c.status = @status'
        params.append({'name': '@status', 'value': status})
    if supplier_id:
        query += ' AND c.supplier_id = @sid'
        params.append({'name': '@sid', 'value': supplier_id})
    if search:
        query += ' AND (CONTAINS(LOWER(c.order_number), @search) OR CONTAINS(LOWER(c.supplier_name), @search))'
        params.append({'name': '@search', 'value': search.lower()})
    query += ' ORDER BY c.created_at DESC'
    items, total = dynamodb.query_items_paged(CONTAINER_PURCHASE_ORDERS, query, params, page, per_page)
    return [PurchaseOrder.from_dict(i) for i in items], total


def get_purchase_order(po_id):
    items = dynamodb.query_items(CONTAINER_PURCHASE_ORDERS,
                                   'SELECT * FROM c WHERE c.id = @id',
                                   [{'name': '@id', 'value': po_id}])
    return PurchaseOrder.from_dict(items[0]) if items else None


def create_purchase_order(data, user_id=''):
    # Count existing POs for order number generation
    count = dynamodb.count_items(CONTAINER_PURCHASE_ORDERS) + 1
    po = PurchaseOrder(
        order_number=PurchaseOrder.generate_order_number(count),
        supplier_id=data.get('supplier_id', ''),
        supplier_name=data.get('supplier_name', ''),
        status='draft',
        items=data.get('items', []),
        tax=float(data.get('tax', 0)),
        shipping=float(data.get('shipping', 0)),
        expected_delivery=data.get('expected_delivery', ''),
        warehouse_id=data.get('warehouse_id', ''),
        notes=data.get('notes', ''),
        created_by=user_id
    )
    # Calculate item totals
    for item in po.items:
        item.calculate_total()
    po.calculate_totals()
    dynamodb.create_item(CONTAINER_PURCHASE_ORDERS, po.to_dict())
    return po


def update_purchase_order(po_id, data, user_id=''):
    po = get_purchase_order(po_id)
    if not po:
        return None
    old_status = po.status
    for field in ['supplier_id', 'supplier_name', 'expected_delivery', 'warehouse_id', 'notes']:
        if field in data:
            setattr(po, field, data[field])
    if 'items' in data:
        po.items = []
        from ..models.purchase_order import PurchaseOrderItem
        for item_data in data['items']:
            item = PurchaseOrderItem.from_dict(item_data)
            item.calculate_total()
            po.items.append(item)
    if 'tax' in data:
        po.tax = float(data['tax'])
    if 'shipping' in data:
        po.shipping = float(data['shipping'])
    po.calculate_totals()
    po.updated_at = datetime.now(timezone.utc).isoformat()
    if old_status != po.status:
        try:
            dynamodb.delete_item(CONTAINER_PURCHASE_ORDERS, po_id, old_status)
        except Exception:
            pass
        dynamodb.create_item(CONTAINER_PURCHASE_ORDERS, po.to_dict())
    else:
        dynamodb.update_item(CONTAINER_PURCHASE_ORDERS, po_id, po.to_dict(), po.status)
    return po


def approve_purchase_order(po_id, user_id=''):
    po = get_purchase_order(po_id)
    if po and po.can_approve():
        old_status = po.status
        po.status = 'approved'
        po.approved_by = user_id
        po.updated_at = datetime.now(timezone.utc).isoformat()
        try:
            dynamodb.delete_item(CONTAINER_PURCHASE_ORDERS, po_id, old_status)
        except Exception:
            pass
        dynamodb.create_item(CONTAINER_PURCHASE_ORDERS, po.to_dict())
        return po
    return None


def receive_purchase_order(po_id, received_items, user_id=''):
    po = get_purchase_order(po_id)
    if po and po.can_receive():
        old_status = po.status
        all_received = True
        for ri in received_items:
            for item in po.items:
                if item.product_id == ri.get('product_id'):
                    item.received_quantity += int(ri.get('quantity', 0))
                    if item.received_quantity < item.quantity:
                        all_received = False
        po.status = 'received' if all_received else 'partial'
        po.updated_at = datetime.now(timezone.utc).isoformat()
        try:
            dynamodb.delete_item(CONTAINER_PURCHASE_ORDERS, po_id, old_status)
        except Exception:
            pass
        dynamodb.create_item(CONTAINER_PURCHASE_ORDERS, po.to_dict())
        return po
    return None


def cancel_purchase_order(po_id, user_id=''):
    po = get_purchase_order(po_id)
    if po and po.can_cancel():
        old_status = po.status
        po.status = 'cancelled'
        po.updated_at = datetime.now(timezone.utc).isoformat()
        try:
            dynamodb.delete_item(CONTAINER_PURCHASE_ORDERS, po_id, old_status)
        except Exception:
            pass
        dynamodb.create_item(CONTAINER_PURCHASE_ORDERS, po.to_dict())
        return po
    return None


def count_purchase_orders(status=''):
    if status:
        return dynamodb.count_items(CONTAINER_PURCHASE_ORDERS,
                                      'SELECT VALUE COUNT(1) FROM c WHERE c.status = @s',
                                      [{'name': '@s', 'value': status}])
    return dynamodb.count_items(CONTAINER_PURCHASE_ORDERS)


# ==================== SALES ORDERS ====================

def get_all_sales_orders(page=1, per_page=25, status='', channel='',
                          search='', sort_by='created_at', sort_order='DESC'):
    query = 'SELECT * FROM c WHERE 1=1'
    params = []
    if status:
        query += ' AND c.status = @status'
        params.append({'name': '@status', 'value': status})
    if channel:
        query += ' AND c.channel = @channel'
        params.append({'name': '@channel', 'value': channel})
    if search:
        query += ' AND (CONTAINS(LOWER(c.order_number), @search) OR CONTAINS(LOWER(c.customer_name), @search))'
        params.append({'name': '@search', 'value': search.lower()})
    query += ' ORDER BY c.created_at DESC'
    items, total = dynamodb.query_items_paged(CONTAINER_SALES_ORDERS, query, params, page, per_page)
    return [SalesOrder.from_dict(i) for i in items], total


def get_sales_order(so_id):
    items = dynamodb.query_items(CONTAINER_SALES_ORDERS,
                                   'SELECT * FROM c WHERE c.id = @id',
                                   [{'name': '@id', 'value': so_id}])
    return SalesOrder.from_dict(items[0]) if items else None


def create_sales_order(data, user_id=''):
    count = dynamodb.count_items(CONTAINER_SALES_ORDERS) + 1
    so = SalesOrder(
        order_number=SalesOrder.generate_order_number(count),
        customer_name=data.get('customer_name', ''),
        customer_email=data.get('customer_email', ''),
        customer_phone=data.get('customer_phone', ''),
        channel=data.get('channel', 'manual'),
        items=data.get('items', []),
        tax=float(data.get('tax', 0)),
        discount=float(data.get('discount', 0)),
        shipping_address=data.get('shipping_address', ''),
        notes=data.get('notes', ''),
        created_by=user_id
    )
    for item in so.items:
        item.calculate_total()
    so.calculate_totals()
    dynamodb.create_item(CONTAINER_SALES_ORDERS, so.to_dict())
    return so


def update_sales_order_status(so_id, new_status, user_id=''):
    so = get_sales_order(so_id)
    if so:
        old_status = so.status
        so.status = new_status
        so.updated_at = datetime.now(timezone.utc).isoformat()
        try:
            dynamodb.delete_item(CONTAINER_SALES_ORDERS, so_id, old_status)
        except Exception:
            pass
        dynamodb.create_item(CONTAINER_SALES_ORDERS, so.to_dict())
        return so
    return None


def cancel_sales_order(so_id, user_id=''):
    return update_sales_order_status(so_id, 'cancelled', user_id)


def get_today_sales():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%dT00:00:00')
    items = dynamodb.query_items(
        CONTAINER_SALES_ORDERS,
        'SELECT c.total_amount FROM c WHERE c.created_at >= @today AND c.status != "cancelled"',
        [{'name': '@today', 'value': today}]
    )
    return sum(i.get('total_amount', 0) for i in items)


def get_monthly_revenue():
    first_of_month = datetime.now(timezone.utc).replace(day=1).strftime('%Y-%m-%dT00:00:00')
    items = dynamodb.query_items(
        CONTAINER_SALES_ORDERS,
        'SELECT c.total_amount FROM c WHERE c.created_at >= @fom AND c.status != "cancelled"',
        [{'name': '@fom', 'value': first_of_month}]
    )
    return sum(i.get('total_amount', 0) for i in items)


def count_sales_orders(status=''):
    if status:
        return dynamodb.count_items(CONTAINER_SALES_ORDERS,
                                      'SELECT VALUE COUNT(1) FROM c WHERE c.status = @s',
                                      [{'name': '@s', 'value': status}])
    return dynamodb.count_items(CONTAINER_SALES_ORDERS)


# ==================== RETURNS ====================

def get_all_returns(page=1, per_page=25, return_type='', status='', search=''):
    query = 'SELECT * FROM c WHERE 1=1'
    params = []
    if return_type:
        query += ' AND c.return_type = @rt'
        params.append({'name': '@rt', 'value': return_type})
    if status:
        query += ' AND c.status = @status'
        params.append({'name': '@status', 'value': status})
    if search:
        query += ' AND CONTAINS(LOWER(c.return_number), @search)'
        params.append({'name': '@search', 'value': search.lower()})
    query += ' ORDER BY c.created_at DESC'
    items, total = dynamodb.query_items_paged(CONTAINER_RETURNS, query, params, page, per_page)
    return [Return.from_dict(i) for i in items], total


def get_return(return_id):
    items = dynamodb.query_items(CONTAINER_RETURNS,
                                   'SELECT * FROM c WHERE c.id = @id',
                                   [{'name': '@id', 'value': return_id}])
    return Return.from_dict(items[0]) if items else None


def create_return(data, user_id=''):
    count = dynamodb.count_items(CONTAINER_RETURNS) + 1
    ret = Return(
        return_number=Return.generate_return_number(count),
        return_type=data.get('return_type', 'customer'),
        order_id=data.get('order_id', ''),
        order_number=data.get('order_number', ''),
        items=data.get('items', []),
        total_refund=float(data.get('total_refund', 0)),
        notes=data.get('notes', ''),
        created_by=user_id
    )
    dynamodb.create_item(CONTAINER_RETURNS, ret.to_dict())
    return ret


def approve_return(return_id, user_id=''):
    ret = get_return(return_id)
    if ret and ret.status == 'pending':
        old_type = ret.return_type
        ret.status = 'approved'
        ret.updated_at = datetime.now(timezone.utc).isoformat()
        dynamodb.update_item(CONTAINER_RETURNS, return_id, ret.to_dict(), old_type)
        return ret
    return None


def process_return(return_id, user_id=''):
    ret = get_return(return_id)
    if ret and ret.status in ('approved', 'received'):
        ret.status = 'processed'
        ret.processed_by = user_id
        ret.updated_at = datetime.now(timezone.utc).isoformat()
        dynamodb.update_item(CONTAINER_RETURNS, return_id, ret.to_dict(), ret.return_type)
        return ret
    return None


def reject_return(return_id, user_id=''):
    ret = get_return(return_id)
    if ret and ret.status == 'pending':
        ret.status = 'rejected'
        ret.updated_at = datetime.now(timezone.utc).isoformat()
        dynamodb.update_item(CONTAINER_RETURNS, return_id, ret.to_dict(), ret.return_type)
        return ret
    return None


def count_returns(return_type=''):
    if return_type:
        return dynamodb.count_items(CONTAINER_RETURNS,
                                      'SELECT VALUE COUNT(1) FROM c WHERE c.return_type = @rt',
                                      [{'name': '@rt', 'value': return_type}])
    return dynamodb.count_items(CONTAINER_RETURNS)


# ==================== SUPPLIERS ====================

def get_all_suppliers(page=1, per_page=25, category='', search='',
                       sort_by='name', sort_order='ASC'):
    query = 'SELECT * FROM c WHERE c.is_active = true'
    params = []
    if category:
        query += ' AND c.category = @cat'
        params.append({'name': '@cat', 'value': category})
    if search:
        query += ' AND (CONTAINS(LOWER(c.name), @search) OR CONTAINS(LOWER(c.code), @search))'
        params.append({'name': '@search', 'value': search.lower()})
    query += ' ORDER BY c.name ASC'
    items, total = dynamodb.query_items_paged(CONTAINER_SUPPLIERS, query, params, page, per_page)
    return [Supplier.from_dict(i) for i in items], total


def get_supplier(supplier_id):
    items = dynamodb.query_items(CONTAINER_SUPPLIERS,
                                   'SELECT * FROM c WHERE c.id = @id',
                                   [{'name': '@id', 'value': supplier_id}])
    return Supplier.from_dict(items[0]) if items else None


def create_supplier(data, user_id=''):
    count = dynamodb.count_items(CONTAINER_SUPPLIERS) + 1
    supplier = Supplier(
        name=data.get('name', ''), code=Supplier.generate_code(count),
        contact_person=data.get('contact_person', ''),
        email=data.get('email', ''), phone=data.get('phone', ''),
        address=data.get('address', {}), category=data.get('category', ''),
        payment_terms=data.get('payment_terms', 'Net 30'),
        lead_time_days=int(data.get('lead_time_days', 7)),
        rating=float(data.get('rating', 0)), notes=data.get('notes', '')
    )
    dynamodb.create_item(CONTAINER_SUPPLIERS, supplier.to_dict())
    return supplier


def update_supplier(supplier_id, data, user_id=''):
    supplier = get_supplier(supplier_id)
    if not supplier:
        return None
    for f in ['name', 'contact_person', 'email', 'phone', 'payment_terms', 'notes']:
        if f in data:
            setattr(supplier, f, data[f])
    if 'address' in data:
        supplier.address = data['address']
    if 'lead_time_days' in data:
        supplier.lead_time_days = int(data['lead_time_days'])
    if 'rating' in data:
        supplier.rating = float(data['rating'])
    if 'category' in data:
        old_cat = supplier.category
        supplier.category = data['category']
        if old_cat != supplier.category:
            try:
                dynamodb.delete_item(CONTAINER_SUPPLIERS, supplier_id, old_cat)
            except Exception:
                pass
            dynamodb.create_item(CONTAINER_SUPPLIERS, supplier.to_dict())
            return supplier
    supplier.updated_at = datetime.now(timezone.utc).isoformat()
    dynamodb.update_item(CONTAINER_SUPPLIERS, supplier_id, supplier.to_dict(), supplier.category)
    return supplier


def deactivate_supplier(supplier_id, user_id=''):
    supplier = get_supplier(supplier_id)
    if supplier:
        supplier.is_active = False
        supplier.updated_at = datetime.now(timezone.utc).isoformat()
        dynamodb.update_item(CONTAINER_SUPPLIERS, supplier_id, supplier.to_dict(), supplier.category)
        return True
    return False


def get_active_suppliers():
    items = dynamodb.query_items(CONTAINER_SUPPLIERS,
                                   'SELECT * FROM c WHERE c.is_active = true ORDER BY c.name ASC')
    return [Supplier.from_dict(i) for i in items]


def count_suppliers():
    return dynamodb.count_items(CONTAINER_SUPPLIERS,
                                  'SELECT VALUE COUNT(1) FROM c WHERE c.is_active = true')


# ==================== WAREHOUSES ====================

def get_all_warehouses(page=1, per_page=25, region='', search=''):
    query = 'SELECT * FROM c WHERE c.is_active = true'
    params = []
    if region:
        query += ' AND c.region = @region'
        params.append({'name': '@region', 'value': region})
    if search:
        query += ' AND CONTAINS(LOWER(c.name), @search)'
        params.append({'name': '@search', 'value': search.lower()})
    query += ' ORDER BY c.name ASC'
    items, total = dynamodb.query_items_paged(CONTAINER_WAREHOUSES, query, params, page, per_page)
    return [Warehouse.from_dict(i) for i in items], total


def get_warehouse(warehouse_id):
    items = dynamodb.query_items(CONTAINER_WAREHOUSES,
                                   'SELECT * FROM c WHERE c.id = @id',
                                   [{'name': '@id', 'value': warehouse_id}])
    return Warehouse.from_dict(items[0]) if items else None


def create_warehouse(data, user_id=''):
    warehouse = Warehouse(
        name=data.get('name', ''), code=data.get('code', ''),
        region=data.get('region', ''), address=data.get('address', {}),
        manager_id=data.get('manager_id', ''),
        capacity=int(data.get('capacity', 10000))
    )
    dynamodb.create_item(CONTAINER_WAREHOUSES, warehouse.to_dict())
    return warehouse


def update_warehouse(warehouse_id, data, user_id=''):
    wh = get_warehouse(warehouse_id)
    if not wh:
        return None
    for f in ['name', 'code', 'manager_id']:
        if f in data:
            setattr(wh, f, data[f])
    if 'address' in data:
        wh.address = data['address']
    if 'capacity' in data:
        wh.capacity = int(data['capacity'])
    if 'region' in data:
        old_region = wh.region
        wh.region = data['region']
        if old_region != wh.region:
            try:
                dynamodb.delete_item(CONTAINER_WAREHOUSES, warehouse_id, old_region)
            except Exception:
                pass
            dynamodb.create_item(CONTAINER_WAREHOUSES, wh.to_dict())
            return wh
    dynamodb.update_item(CONTAINER_WAREHOUSES, warehouse_id, wh.to_dict(), wh.region)
    return wh


def get_active_warehouses():
    items = dynamodb.query_items(CONTAINER_WAREHOUSES,
                                   'SELECT * FROM c WHERE c.is_active = true ORDER BY c.name ASC')
    return [Warehouse.from_dict(i) for i in items]


def count_warehouses():
    return dynamodb.count_items(CONTAINER_WAREHOUSES)
