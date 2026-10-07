"""
Dashboard routes.
"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user

bp = Blueprint('dashboard', __name__, url_prefix='/')


@bp.route('/')
@login_required
def index():
    from ..services.product_service import count_products
    from ..services.inventory_service import get_low_stock_items, get_inventory_value
    from ..services.order_service import (count_purchase_orders, count_sales_orders,
                                           get_today_sales, get_monthly_revenue,
                                           get_all_sales_orders)

    total_products = count_products()
    inventory_value = get_inventory_value()
    pending_orders = count_purchase_orders('pending') + count_sales_orders('pending')
    low_stock_items = get_low_stock_items()
    today_sales = get_today_sales()
    monthly_revenue = get_monthly_revenue()
    recent_orders, _ = get_all_sales_orders(page=1, per_page=5)

    return render_template('dashboard/index.html',
                           total_products=total_products,
                           inventory_value=inventory_value,
                           pending_orders=pending_orders,
                           low_stock_count=len(low_stock_items),
                           low_stock_items=low_stock_items[:5],
                           today_sales=today_sales,
                           monthly_revenue=monthly_revenue,
                           recent_orders=recent_orders)
