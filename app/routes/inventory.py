"""
Inventory routes.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user

bp = Blueprint('inventory', __name__, url_prefix='/inventory')


@bp.route('/')
@login_required
def list_inventory():
    from ..services.inventory_service import get_all_inventory
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    inventory, total = get_all_inventory(page=page, per_page=25, search=search)
    return render_template('inventory/list.html', inventory=inventory, total=total)


@bp.route('/adjust', methods=['GET', 'POST'])
@login_required
def adjust_stock():
    from ..services.inventory_service import adjust_stock as do_adjust, transfer_stock
    from ..services.product_service import get_all_products
    from ..services.order_service import get_active_warehouses
    if request.method == 'POST':
        movement_type = request.form.get('movement_type')
        product_id = request.form.get('product_id')
        warehouse_id = request.form.get('warehouse_id')
        quantity = int(request.form.get('quantity', 0))
        reason = request.form.get('reason', '')
        try:
            if movement_type == 'transfer':
                dest = request.form.get('dest_warehouse_id')
                transfer_stock(product_id, warehouse_id, dest, quantity,
                               current_user.id, current_user.full_name)
            else:
                do_adjust(product_id, warehouse_id, quantity, movement_type,
                          reason=reason, user_id=current_user.id,
                          user_name=current_user.full_name)
            flash('Stock adjusted successfully!', 'success')
            return redirect(url_for('inventory.list_inventory'))
        except Exception as e:
            flash(f'Error: {e}', 'error')
    products, _ = get_all_products(page=1, per_page=500)
    warehouses = get_active_warehouses()
    return render_template('inventory/movement_form.html', products=products, warehouses=warehouses)


@bp.route('/movements')
@login_required
def movement_history():
    from ..services.inventory_service import get_movement_history
    page = request.args.get('page', 1, type=int)
    movements, total = get_movement_history(page=page, per_page=25)
    return render_template('inventory/movement_history.html', movements=movements, total=total)


@bp.route('/barcode')
@login_required
def barcode_scan():
    return render_template('inventory/barcode_scan.html')


@bp.route('/export')
@login_required
def export_inventory():
    from ..services.inventory_service import get_all_inventory
    from ..services.additional_services import generate_excel_report
    inventory, _ = get_all_inventory(page=1, per_page=5000)
    headers = ['Product', 'SKU', 'Warehouse', 'Qty', 'Reserved', 'Available', 'Location']
    data = [[i.product_name, i.sku, i.warehouse_name, i.quantity, i.reserved_quantity, i.available_quantity, i.location] for i in inventory]
    excel = generate_excel_report('Inventory', headers, data, 'inventory.xlsx')
    return Response(excel, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={'Content-Disposition': 'attachment;filename=inventory.xlsx'})
