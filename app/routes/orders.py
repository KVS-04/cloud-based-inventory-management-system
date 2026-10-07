"""
Purchase Order, Sales Order, Returns, Suppliers, Warehouses routes.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..utils.decorators import manager_required

# ==================== PURCHASE ORDERS ====================
po_bp = Blueprint('purchase_orders', __name__, url_prefix='/purchase-orders')

@po_bp.route('/')
@login_required
def list_purchase_orders():
    from ..services.order_service import get_all_purchase_orders
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    orders, total = get_all_purchase_orders(page=page, per_page=25, status=status, search=search)
    return render_template('purchase_orders/list.html', orders=orders, total=total, current_status=status)

@po_bp.route('/<id>')
@login_required
def view_purchase_order(id):
    from ..services.order_service import get_purchase_order
    po = get_purchase_order(id)
    if not po:
        flash('Purchase order not found.', 'error')
        return redirect(url_for('purchase_orders.list_purchase_orders'))
    return render_template('purchase_orders/detail.html', po=po)

@po_bp.route('/add', methods=['GET', 'POST'])
@manager_required
def add_purchase_order():
    from ..services.order_service import create_purchase_order, get_active_suppliers, get_active_warehouses
    if request.method == 'POST':
        data = request.form.to_dict()
        # Parse line items from form
        items = []
        i = 0
        while f'items[{i}][product_name]' in request.form:
            items.append({
                'product_name': request.form.get(f'items[{i}][product_name]'),
                'quantity': int(request.form.get(f'items[{i}][quantity]', 0)),
                'unit_price': float(request.form.get(f'items[{i}][unit_price]', 0))
            })
            i += 1
        data['items'] = items
        po = create_purchase_order(data, current_user.id)
        flash(f'Purchase order {po.order_number} created!', 'success')
        return redirect(url_for('purchase_orders.view_purchase_order', id=po.id))
    suppliers = get_active_suppliers()
    warehouses = get_active_warehouses()
    return render_template('purchase_orders/form.html', po=None, suppliers=suppliers, warehouses=warehouses)

@po_bp.route('/<id>/approve', methods=['POST'])
@manager_required
def approve_po(id):
    from ..services.order_service import approve_purchase_order
    po = approve_purchase_order(id, current_user.id)
    flash(f'PO {po.order_number} approved!' if po else 'Cannot approve this order.', 'success' if po else 'error')
    return redirect(url_for('purchase_orders.view_purchase_order', id=id))

@po_bp.route('/<id>/receive', methods=['POST'])
@manager_required
def receive_po(id):
    from ..services.order_service import receive_purchase_order
    po = receive_purchase_order(id, [], current_user.id)
    flash('Items received.' if po else 'Cannot receive this order.', 'success' if po else 'error')
    return redirect(url_for('purchase_orders.view_purchase_order', id=id))

@po_bp.route('/<id>/cancel', methods=['POST'])
@manager_required
def cancel_po(id):
    from ..services.order_service import cancel_purchase_order
    po = cancel_purchase_order(id, current_user.id)
    flash('PO cancelled.' if po else 'Cannot cancel.', 'success' if po else 'error')
    return redirect(url_for('purchase_orders.view_purchase_order', id=id))


# ==================== SALES ORDERS ====================
so_bp = Blueprint('sales_orders', __name__, url_prefix='/sales-orders')

@so_bp.route('/')
@login_required
def list_sales_orders():
    from ..services.order_service import get_all_sales_orders
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    orders, total = get_all_sales_orders(page=page, per_page=25, status=status, search=search)
    return render_template('sales_orders/list.html', orders=orders, total=total, current_status=status)

@so_bp.route('/<id>')
@login_required
def view_sales_order(id):
    from ..services.order_service import get_sales_order
    so = get_sales_order(id)
    if not so:
        flash('Sales order not found.', 'error')
        return redirect(url_for('sales_orders.list_sales_orders'))
    return render_template('sales_orders/detail.html', so=so)

@so_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_sales_order():
    from ..services.order_service import create_sales_order
    if request.method == 'POST':
        data = request.form.to_dict()
        items = []
        i = 0
        while f'items[{i}][product_name]' in request.form:
            items.append({
                'product_name': request.form.get(f'items[{i}][product_name]'),
                'quantity': int(request.form.get(f'items[{i}][quantity]', 0)),
                'unit_price': float(request.form.get(f'items[{i}][unit_price]', 0))
            })
            i += 1
        data['items'] = items
        so = create_sales_order(data, current_user.id)
        flash(f'Sales order {so.order_number} created!', 'success')
        return redirect(url_for('sales_orders.view_sales_order', id=so.id))
    return render_template('sales_orders/form.html', so=None)

@so_bp.route('/<id>/status', methods=['POST'])
@login_required
def update_so_status(id):
    from ..services.order_service import update_sales_order_status
    new_status = request.form.get('status')
    so = update_sales_order_status(id, new_status, current_user.id)
    flash(f'Status updated to {new_status}.' if so else 'Error.', 'success' if so else 'error')
    return redirect(url_for('sales_orders.view_sales_order', id=id))


# ==================== RETURNS ====================
ret_bp = Blueprint('returns', __name__, url_prefix='/returns')

@ret_bp.route('/')
@login_required
def list_returns():
    from ..services.order_service import get_all_returns
    rtype = request.args.get('type', '')
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    returns, total = get_all_returns(page=page, per_page=25, return_type=rtype, status=status)
    return render_template('returns/list.html', returns=returns, total=total)

@ret_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_return():
    if request.method == 'POST':
        from ..services.order_service import create_return
        data = request.form.to_dict()
        items = []
        i = 0
        while f'items[{i}][product_name]' in request.form:
            items.append({
                'product_name': request.form.get(f'items[{i}][product_name]'),
                'quantity': int(request.form.get(f'items[{i}][quantity]', 0)),
                'reason': request.form.get(f'items[{i}][reason]', ''),
                'condition': request.form.get(f'items[{i}][condition]', 'new')
            })
            i += 1
        data['items'] = items
        ret = create_return(data, current_user.id)
        flash(f'Return {ret.return_number} created!', 'success')
        return redirect(url_for('returns.list_returns'))
    return render_template('returns/form.html')

@ret_bp.route('/<id>/approve', methods=['POST'])
@manager_required
def approve_ret(id):
    from ..services.order_service import approve_return
    approve_return(id, current_user.id)
    flash('Return approved.', 'success')
    return redirect(url_for('returns.list_returns'))


# ==================== SUPPLIERS ====================
sup_bp = Blueprint('suppliers', __name__, url_prefix='/suppliers')

@sup_bp.route('/')
@login_required
def list_suppliers():
    from ..services.order_service import get_all_suppliers
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    suppliers, total = get_all_suppliers(page=page, per_page=25, search=search)
    return render_template('suppliers/list.html', suppliers=suppliers, total=total)

@sup_bp.route('/add', methods=['GET', 'POST'])
@manager_required
def add_supplier():
    if request.method == 'POST':
        from ..services.order_service import create_supplier
        data = request.form.to_dict()
        data['address'] = {
            'street': request.form.get('street', ''), 'city': request.form.get('city', ''),
            'state': request.form.get('state', ''), 'zip': request.form.get('zip', ''),
            'country': request.form.get('country', '')
        }
        create_supplier(data, current_user.id)
        flash('Supplier created!', 'success')
        return redirect(url_for('suppliers.list_suppliers'))
    return render_template('suppliers/form.html', supplier=None)

@sup_bp.route('/<id>/edit', methods=['GET', 'POST'])
@manager_required
def edit_supplier(id):
    from ..services.order_service import get_supplier, update_supplier
    supplier = get_supplier(id)
    if not supplier:
        flash('Supplier not found.', 'error')
        return redirect(url_for('suppliers.list_suppliers'))
    if request.method == 'POST':
        data = request.form.to_dict()
        data['address'] = {
            'street': request.form.get('street', ''), 'city': request.form.get('city', ''),
            'state': request.form.get('state', ''), 'zip': request.form.get('zip', ''),
            'country': request.form.get('country', '')
        }
        update_supplier(id, data, current_user.id)
        flash('Supplier updated.', 'success')
        return redirect(url_for('suppliers.list_suppliers'))
    return render_template('suppliers/form.html', supplier=supplier)


# ==================== WAREHOUSES ====================
wh_bp = Blueprint('warehouses', __name__, url_prefix='/warehouses')

@wh_bp.route('/')
@login_required
def list_warehouses():
    from ..services.order_service import get_all_warehouses
    page = request.args.get('page', 1, type=int)
    warehouses, total = get_all_warehouses(page=page, per_page=25)
    return render_template('warehouses/list.html', warehouses=warehouses, total=total)

@wh_bp.route('/add', methods=['GET', 'POST'])
@manager_required
def add_warehouse():
    if request.method == 'POST':
        from ..services.order_service import create_warehouse
        data = request.form.to_dict()
        data['address'] = {
            'street': request.form.get('street', ''), 'city': request.form.get('city', ''),
            'state': request.form.get('state', ''), 'zip': request.form.get('zip', ''),
            'country': request.form.get('country', '')
        }
        create_warehouse(data, current_user.id)
        flash('Warehouse created!', 'success')
        return redirect(url_for('warehouses.list_warehouses'))
    return render_template('warehouses/form.html', warehouse=None)

@wh_bp.route('/<id>/edit', methods=['GET', 'POST'])
@manager_required
def edit_warehouse(id):
    from ..services.order_service import get_warehouse, update_warehouse
    warehouse = get_warehouse(id)
    if not warehouse:
        flash('Warehouse not found.', 'error')
        return redirect(url_for('warehouses.list_warehouses'))
    if request.method == 'POST':
        data = request.form.to_dict()
        data['address'] = {
            'street': request.form.get('street', ''), 'city': request.form.get('city', ''),
            'state': request.form.get('state', ''), 'zip': request.form.get('zip', ''),
            'country': request.form.get('country', '')
        }
        update_warehouse(id, data, current_user.id)
        flash('Warehouse updated.', 'success')
        return redirect(url_for('warehouses.list_warehouses'))
    return render_template('warehouses/form.html', warehouse=warehouse)
