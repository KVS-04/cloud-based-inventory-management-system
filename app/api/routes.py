"""
REST API endpoints for Products, Inventory, Dashboard, Barcode, Notifications.
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user
from ..utils.decorators import login_required_api, api_manager_required

api_bp = Blueprint('api', __name__, url_prefix='/api')


def success_response(data=None, message='Success', status=200):
    return jsonify({'success': True, 'message': message, 'data': data}), status


def error_response(message='Error', status=400):
    return jsonify({'success': False, 'message': message}), status


# ==================== PRODUCTS API ====================

@api_bp.route('/products', methods=['GET'])
@login_required_api
def api_get_products():
    from ..services.product_service import get_all_products
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    products, total = get_all_products(page=page, per_page=per_page, search=search, category=category)
    return success_response({
        'items': [p.to_dict() for p in products],
        'total': total, 'page': page, 'per_page': per_page
    })


@api_bp.route('/products/<id>', methods=['GET'])
@login_required_api
def api_get_product(id):
    from ..services.product_service import get_product_by_id
    product = get_product_by_id(id)
    if not product:
        return error_response('Product not found', 404)
    return success_response(product.to_dict())


@api_bp.route('/products', methods=['POST'])
@api_manager_required
def api_create_product():
    from ..services.product_service import create_product
    data = request.get_json()
    if not data:
        return error_response('No data provided')
    product, errors = create_product(data)
    if product:
        return success_response(product.to_dict(), 'Product created', 201)
    return error_response('; '.join(errors))


@api_bp.route('/products/<id>', methods=['PUT'])
@api_manager_required
def api_update_product(id):
    from ..services.product_service import update_product
    data = request.get_json()
    product, errors = update_product(id, data)
    if product:
        return success_response(product.to_dict(), 'Product updated')
    return error_response('; '.join(errors))


@api_bp.route('/products/<id>', methods=['DELETE'])
@api_manager_required
def api_delete_product(id):
    from ..services.product_service import delete_product
    if delete_product(id):
        return success_response(message='Product deleted')
    return error_response('Product not found', 404)


# ==================== INVENTORY API ====================

@api_bp.route('/inventory', methods=['GET'])
@login_required_api
def api_get_inventory():
    from ..services.inventory_service import get_all_inventory
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    inventory, total = get_all_inventory(page=page, per_page=per_page)
    return success_response({
        'items': [i.to_dict() for i in inventory],
        'total': total
    })


@api_bp.route('/inventory/adjust', methods=['POST'])
@login_required_api
def api_adjust_stock():
    from ..services.inventory_service import adjust_stock
    data = request.get_json() or request.form.to_dict()
    try:
        inv, movement = adjust_stock(
            product_id=data.get('product_id'),
            warehouse_id=data.get('warehouse_id', ''),
            quantity_change=int(data.get('quantity', 0)),
            movement_type=data.get('movement_type', 'adjustment'),
            reason=data.get('reason', ''),
            user_id=current_user.id if current_user.is_authenticated else '',
            user_name=current_user.full_name if current_user.is_authenticated else ''
        )
        return success_response({
            'inventory': inv.to_dict(),
            'movement': movement.to_dict()
        }, 'Stock adjusted')
    except Exception as e:
        return error_response(str(e))


@api_bp.route('/inventory/movements', methods=['GET'])
@login_required_api
def api_get_movements():
    from ..services.inventory_service import get_movement_history
    page = request.args.get('page', 1, type=int)
    movements, total = get_movement_history(page=page, per_page=25)
    return success_response({
        'items': [m.to_dict() for m in movements],
        'total': total
    })


# ==================== BARCODE API ====================

@api_bp.route('/barcode/lookup', methods=['POST'])
@login_required_api
def api_barcode_lookup():
    from ..services.additional_services import lookup_by_barcode
    data = request.get_json()
    barcode = data.get('barcode', '')
    if not barcode:
        return error_response('Barcode is required')
    product = lookup_by_barcode(barcode)
    if product:
        return success_response(product.to_dict())
    return error_response('Product not found for this barcode', 404)


@api_bp.route('/barcode/generate', methods=['POST'])
@login_required_api
def api_generate_barcode():
    from ..services.additional_services import generate_barcode_number
    barcode = generate_barcode_number()
    return success_response({'barcode': barcode})


# ==================== DASHBOARD API ====================

@api_bp.route('/dashboard/stats', methods=['GET'])
@login_required_api
def api_dashboard_stats():
    from ..services.product_service import count_products
    from ..services.inventory_service import get_inventory_value, get_stock_summary
    from ..services.order_service import count_purchase_orders, count_sales_orders, get_today_sales, get_monthly_revenue
    return success_response({
        'total_products': count_products(),
        'inventory_value': get_inventory_value(),
        'pending_orders': count_purchase_orders('pending') + count_sales_orders('pending'),
        'stock_summary': get_stock_summary(),
        'today_sales': get_today_sales(),
        'monthly_revenue': get_monthly_revenue()
    })


@api_bp.route('/dashboard/charts/<chart_type>', methods=['GET'])
@login_required_api
def api_dashboard_chart(chart_type):
    # Return empty data - charts use fallback sample data in JS
    return success_response(None)


# ==================== NOTIFICATIONS API ====================

@api_bp.route('/notifications/unread-count', methods=['GET'])
@login_required_api
def api_unread_count():
    from ..services.additional_services import get_unread_count
    user_id = current_user.id if current_user.is_authenticated else ''
    count = get_unread_count(user_id)
    return success_response(count)


@api_bp.route('/notifications/read-all', methods=['PUT'])
@login_required_api
def api_mark_all_read():
    from ..services.additional_services import mark_all_as_read
    user_id = current_user.id if current_user.is_authenticated else ''
    count = mark_all_as_read(user_id)
    return success_response({'marked': count})


# ==================== FORECASTING API ====================

@api_bp.route('/forecast/<product_id>', methods=['GET'])
@login_required_api
def api_forecast(product_id):
    from ..services.additional_services import get_demand_forecast
    days = request.args.get('days', 30, type=int)
    result = get_demand_forecast(product_id, days)
    return success_response(result)


@api_bp.route('/forecast/reorder-suggestions', methods=['GET'])
@login_required_api
def api_reorder_suggestions():
    from ..services.additional_services import get_reorder_suggestions
    return success_response(get_reorder_suggestions())


# ==================== ORDERS API ====================

@api_bp.route('/purchase-orders', methods=['GET'])
@login_required_api
def api_get_purchase_orders():
    from ..services.order_service import get_all_purchase_orders
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    orders, total = get_all_purchase_orders(page=page, per_page=25, status=status)
    return success_response({'items': [o.to_dict() for o in orders], 'total': total})


@api_bp.route('/sales-orders', methods=['GET'])
@login_required_api
def api_get_sales_orders():
    from ..services.order_service import get_all_sales_orders
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    orders, total = get_all_sales_orders(page=page, per_page=25, status=status)
    return success_response({'items': [o.to_dict() for o in orders], 'total': total})


@api_bp.route('/suppliers', methods=['GET'])
@login_required_api
def api_get_suppliers():
    from ..services.order_service import get_all_suppliers
    suppliers, total = get_all_suppliers(page=1, per_page=100)
    return success_response({'items': [s.to_dict() for s in suppliers], 'total': total})


@api_bp.route('/warehouses', methods=['GET'])
@login_required_api
def api_get_warehouses():
    from ..services.order_service import get_all_warehouses
    warehouses, total = get_all_warehouses(page=1, per_page=100)
    return success_response({'items': [w.to_dict() for w in warehouses], 'total': total})
