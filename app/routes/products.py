"""
Product routes.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from ..utils.decorators import manager_required
from ..utils.constants import PRODUCT_CATEGORIES, PRODUCT_UNITS

bp = Blueprint('products', __name__, url_prefix='/products')


@bp.route('/')
@login_required
def list_products():
    from ..services.product_service import get_all_products, get_product_categories
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    products, total = get_all_products(page=page, per_page=25, search=search, category=category)
    categories = get_product_categories() or PRODUCT_CATEGORIES
    return render_template('products/list.html', products=products, categories=categories, total=total)


@bp.route('/<id>')
@login_required
def view_product(id):
    from ..services.product_service import get_product_by_id
    product = get_product_by_id(id)
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('products.list_products'))
    return render_template('products/detail.html', product=product)


@bp.route('/add', methods=['GET', 'POST'])
@manager_required
def add_product():
    from ..services.product_service import create_product
    from ..services.order_service import get_active_suppliers
    if request.method == 'POST':
        product, errors = create_product(request.form.to_dict(), current_user.id)
        if product:
            # Handle image upload
            if 'image' in request.files and request.files['image'].filename:
                try:
                    from ..services.s3_service import s3_storage
                    url = s3_storage.upload_product_image(request.files['image'], product.id)
                    from ..services.product_service import update_product
                    update_product(product.id, {'image_url': url})
                except Exception:
                    pass
            flash('Product created successfully!', 'success')
            return redirect(url_for('products.view_product', id=product.id))
        for err in errors:
            flash(err, 'error')
    suppliers = get_active_suppliers()
    return render_template('products/form.html', product=None,
                           categories=PRODUCT_CATEGORIES, units=PRODUCT_UNITS, suppliers=suppliers)


@bp.route('/<id>/edit', methods=['GET', 'POST'])
@manager_required
def edit_product(id):
    from ..services.product_service import get_product_by_id, update_product
    from ..services.order_service import get_active_suppliers
    product = get_product_by_id(id)
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('products.list_products'))
    if request.method == 'POST':
        updated, errors = update_product(id, request.form.to_dict(), current_user.id)
        if updated:
            if 'image' in request.files and request.files['image'].filename:
                try:
                    from ..services.s3_service import s3_storage
                    url = s3_storage.upload_product_image(request.files['image'], updated.id)
                    update_product(updated.id, {'image_url': url})
                except Exception:
                    pass
            flash('Product updated.', 'success')
            return redirect(url_for('products.view_product', id=id))
        for err in errors:
            flash(err, 'error')
    suppliers = get_active_suppliers()
    return render_template('products/form.html', product=product,
                           categories=PRODUCT_CATEGORIES, units=PRODUCT_UNITS, suppliers=suppliers)


@bp.route('/<id>/delete', methods=['POST'])
@manager_required
def delete_product(id):
    from ..services.product_service import delete_product
    if delete_product(id, current_user.id):
        flash('Product deleted.', 'success')
    else:
        flash('Product not found.', 'error')
    return redirect(url_for('products.list_products'))


@bp.route('/export')
@login_required
def export_products(format='excel'):
    from ..services.product_service import get_all_products
    from ..services.additional_services import generate_excel_report
    products, _ = get_all_products(page=1, per_page=1000)
    headers = ['SKU', 'Name', 'Category', 'Price', 'Cost', 'Unit']
    data = [[p.sku, p.name, p.category, p.price, p.cost_price, p.unit] for p in products]
    excel_data = generate_excel_report('Products', headers, data, 'products.xlsx')
    return Response(excel_data, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={'Content-Disposition': 'attachment;filename=products.xlsx'})
