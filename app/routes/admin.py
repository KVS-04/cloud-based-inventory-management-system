"""
Reports, Users, Notifications, Audit Logs routes.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from ..utils.decorators import admin_required, manager_required

# ==================== REPORTS ====================
reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@manager_required
def index():
    return render_template('reports/index.html')

@reports_bp.route('/generate', methods=['POST'])
@manager_required
def generate_report():
    from ..services.additional_services import generate_excel_report, generate_pdf_report
    from ..services.product_service import get_all_products
    from ..services.inventory_service import get_all_inventory
    report_type = request.form.get('report_type', 'inventory_summary')
    fmt = request.form.get('format', 'excel')

    if report_type == 'inventory_summary':
        inventory, _ = get_all_inventory(page=1, per_page=5000)
        headers = ['Product', 'SKU', 'Warehouse', 'Qty', 'Available', 'Location']
        data = [[i.product_name, i.sku, i.warehouse_name, i.quantity, i.available_quantity, i.location] for i in inventory]
        title = 'Inventory Summary Report'
    elif report_type == 'sales_report':
        from ..services.order_service import get_all_sales_orders
        orders, _ = get_all_sales_orders(page=1, per_page=5000)
        headers = ['Order#', 'Customer', 'Channel', 'Total', 'Status', 'Date']
        data = [[o.order_number, o.customer_name, o.channel, o.total_amount, o.status, o.created_at[:10]] for o in orders]
        title = 'Sales Report'
    elif report_type == 'low_stock':
        from ..services.inventory_service import get_low_stock_items
        items = get_low_stock_items()
        headers = ['Product', 'Current Stock', 'Warehouse']
        data = [[i.product_name, i.quantity, i.warehouse_name] for i in items]
        title = 'Low Stock Report'
    else:
        products, _ = get_all_products(page=1, per_page=5000)
        headers = ['SKU', 'Name', 'Category', 'Price', 'Cost']
        data = [[p.sku, p.name, p.category, p.price, p.cost_price] for p in products]
        title = 'Product Report'

    if fmt == 'pdf':
        content = generate_pdf_report(title, headers, data, f'{report_type}.pdf')
        return Response(content, mimetype='application/pdf',
                        headers={'Content-Disposition': f'attachment;filename={report_type}.pdf'})
    else:
        content = generate_excel_report(title, headers, data, f'{report_type}.xlsx')
        return Response(content, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        headers={'Content-Disposition': f'attachment;filename={report_type}.xlsx'})

@reports_bp.route('/view/<report_type>')
@manager_required
def view_report(report_type):
    return render_template('reports/view.html', report_type=report_type)


# ==================== USER MANAGEMENT ====================
users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/')
@admin_required
def list_users():
    from ..services.auth_service import get_all_users
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    users, total = get_all_users(page=page, per_page=25, search=search)
    return render_template('users/list.html', users=users, total=total)

@users_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        from ..services.auth_service import create_user, get_user_by_email
        from ..utils.validators import validate_email
        data = request.form.to_dict()
        if not validate_email(data.get('email', '')):
            flash('Invalid email.', 'error')
            return render_template('users/form.html', user=None)
        if get_user_by_email(data['email']):
            flash('Email exists.', 'error')
            return render_template('users/form.html', user=None)
        if data.get('password') != data.get('confirm_password'):
            flash('Passwords do not match.', 'error')
            return render_template('users/form.html', user=None)
        create_user(data)
        flash('User created!', 'success')
        return redirect(url_for('users.list_users'))
    return render_template('users/form.html', user=None)

@users_bp.route('/<id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(id):
    from ..services.auth_service import get_user_by_id, update_user
    user = get_user_by_id(id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('users.list_users'))
    if request.method == 'POST':
        data = request.form.to_dict()
        if not data.get('password'):
            data.pop('password', None)
        update_user(id, data)
        flash('User updated.', 'success')
        return redirect(url_for('users.list_users'))
    return render_template('users/form.html', user=user)

@users_bp.route('/<id>/toggle', methods=['POST'])
@admin_required
def toggle_user(id):
    from ..services.auth_service import toggle_user_active
    user = toggle_user_active(id)
    flash(f'User {"activated" if user and user.is_active else "deactivated"}.', 'success')
    return redirect(url_for('users.list_users'))

@users_bp.route('/<id>/delete', methods=['POST'])
@admin_required
def delete_user(id):
    from ..services.auth_service import delete_user as do_delete
    if id == current_user.id:
        flash('You cannot delete yourself!', 'error')
    else:
        if do_delete(id):
            flash('User deleted successfully.', 'success')
        else:
            flash('User not found.', 'error')
    return redirect(url_for('users.list_users'))


# ==================== NOTIFICATIONS ====================
notif_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notif_bp.route('/')
@login_required
def list_notifications():
    from ..services.additional_services import get_user_notifications
    page = request.args.get('page', 1, type=int)
    unread = request.args.get('unread') == '1'
    notifications, total = get_user_notifications(current_user.id, page=page, unread_only=unread)
    return render_template('notifications/list.html', notifications=notifications, total=total)

@notif_bp.route('/<id>/read', methods=['POST'])
@login_required
def mark_read(id):
    from ..services.additional_services import mark_as_read
    mark_as_read(id, current_user.id)
    return redirect(url_for('notifications.list_notifications'))


# ==================== AUDIT LOGS ====================
audit_bp = Blueprint('audit_logs', __name__, url_prefix='/audit-logs')

@audit_bp.route('/')
@admin_required
def list_audit_logs():
    from ..services.additional_services import get_audit_logs
    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id', '')
    action = request.args.get('action', '')
    entity_type = request.args.get('entity_type', '')
    logs, total = get_audit_logs(page=page, per_page=25, user_id=user_id,
                                  action=action, entity_type=entity_type)
    return render_template('audit_logs/list.html', logs=logs, total=total)

@audit_bp.route('/export')
@admin_required
def export_audit_logs():
    from ..services.additional_services import export_audit_logs
    fmt = request.args.get('format', 'excel')
    filters = {
        'user_id': request.args.get('user_id', ''),
        'action': request.args.get('action', ''),
        'entity_type': request.args.get('entity_type', '')
    }
    data = export_audit_logs(filters, fmt)
    if fmt == 'pdf':
        return Response(data, mimetype='application/pdf',
                        headers={'Content-Disposition': 'attachment;filename=audit_logs.pdf'})
    return Response(data, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={'Content-Disposition': 'attachment;filename=audit_logs.xlsx'})
