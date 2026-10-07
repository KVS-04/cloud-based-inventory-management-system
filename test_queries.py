"""Quick test script to debug Cosmos DB queries."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app
from app.services.cosmos_db_service import cosmos_db

app = create_app()
with app.app_context():
    print("--- Testing purchase_orders ---")
    items = cosmos_db.query_items("purchase_orders", "SELECT * FROM c")
    print(f"Raw query returned {len(items)} items")
    for i in items:
        print(f"  PO: {i.get('order_number')} status={i.get('status')}")

    print("\n--- Testing sales_orders ---")
    items2 = cosmos_db.query_items("sales_orders", "SELECT * FROM c")
    print(f"Raw query returned {len(items2)} items")
    for i in items2:
        print(f"  SO: {i.get('order_number')} customer={i.get('customer_name')}")

    print("\n--- Testing users ---")
    items3 = cosmos_db.query_items("users", "SELECT * FROM c")
    print(f"Raw query returned {len(items3)} items")

    print("\n--- Testing paged query (PO with WHERE 1=1) ---")
    paged_items, total = cosmos_db.query_items_paged(
        "purchase_orders",
        "SELECT * FROM c WHERE 1=1 ORDER BY c.created_at DESC",
        [], 1, 25
    )
    print(f"Paged query returned {len(paged_items)} items, total={total}")
