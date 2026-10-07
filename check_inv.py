import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app
from app.services.cosmos_db_service import cosmos_db

app = create_app()
with app.app_context():
    items = cosmos_db.query_items('inventory', 'SELECT * FROM c')
    for i in items:
        print(f"Inventory ID: {i.get('id')}, Product: {i.get('product_name')}, SKU: {i.get('sku')}, Qty: {i.get('quantity')}, Location: {i.get('location')}")
