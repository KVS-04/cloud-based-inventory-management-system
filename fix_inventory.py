import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app
from app.services.cosmos_db_service import cosmos_db

app = create_app()
with app.app_context():
    items = cosmos_db.query_items('inventory', 'SELECT * FROM c')
    for i in items:
        if not i.get('product_name') and not i.get('sku'):
            print(f"Deleting invalid inventory record: {i.get('id')}")
            # The partition key for inventory is warehouse_id, let's get it first
            warehouse_id = i.get('warehouse_id', '')
            cosmos_db.delete_item('inventory', i.get('id'), warehouse_id)
            print("Deleted successfully.")
