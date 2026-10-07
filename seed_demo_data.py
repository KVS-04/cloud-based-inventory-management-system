"""
Seed script to populate Azure Cosmos DB with demo data.
Run this script once to add 2 example items for each category.
"""

import sys
import os
import uuid
from datetime import datetime, timezone, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.cosmos_db_service import cosmos_db
from app.utils.constants import (
    CONTAINER_PRODUCTS, CONTAINER_SUPPLIERS, CONTAINER_WAREHOUSES,
    CONTAINER_INVENTORY, CONTAINER_PURCHASE_ORDERS, CONTAINER_SALES_ORDERS,
    CONTAINER_NOTIFICATIONS, CONTAINER_USERS
)

app = create_app()

def seed_data():
    with app.app_context():
        print("\n" + "=" * 60)
        print("🌱 SEEDING DEMO DATA INTO AZURE COSMOS DB")
        print("=" * 60)

        now = datetime.now(timezone.utc).isoformat()

        # ─────────────────────────────────────────
        # 1. SUPPLIERS (2 items)
        # ─────────────────────────────────────────
        print("\n📦 Creating Suppliers...")
        suppliers = [
            {
                "id": str(uuid.uuid4()),
                "name": "TechVision Electronics Ltd.",
                "code": "SUP-001",
                "contact_person": "Rajesh Kumar",
                "email": "rajesh@techvision.com",
                "phone": "+91-9876543210",
                "address": {
                    "street": "45 Industrial Area, Phase 2",
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "zip": "560058",
                    "country": "India"
                },
                "category": "Electronics",
                "payment_terms": "Net 30",
                "lead_time_days": 7,
                "rating": 4.5,
                "is_active": True,
                "notes": "Premium electronics supplier with fast delivery.",
                "created_at": now,
                "updated_at": now
            },
            {
                "id": str(uuid.uuid4()),
                "name": "FurniCraft Industries",
                "code": "SUP-002",
                "contact_person": "Priya Sharma",
                "email": "priya@furnicraft.in",
                "phone": "+91-8765432109",
                "address": {
                    "street": "12 Woodworkers Lane",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "zip": "400072",
                    "country": "India"
                },
                "category": "Home & Garden",
                "payment_terms": "Net 45",
                "lead_time_days": 14,
                "rating": 4.0,
                "is_active": True,
                "notes": "Specializes in office and home furniture.",
                "created_at": now,
                "updated_at": now
            }
        ]

        for s in suppliers:
            try:
                cosmos_db.create_item(CONTAINER_SUPPLIERS, s)
                print(f"  ✅ Supplier: {s['name']}")
            except Exception as e:
                print(f"  ⚠️  Supplier {s['name']}: {e}")

        # ─────────────────────────────────────────
        # 2. WAREHOUSES (2 items)
        # ─────────────────────────────────────────
        print("\n🏭 Creating Warehouses...")
        wh1_id = str(uuid.uuid4())
        wh2_id = str(uuid.uuid4())
        warehouses = [
            {
                "id": wh1_id,
                "name": "Central Warehouse - Bangalore",
                "code": "WH-BLR-01",
                "region": "South",
                "address": {
                    "street": "Plot 78, Whitefield Tech Park",
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "zip": "560066",
                    "country": "India"
                },
                "manager_id": "",
                "capacity": 50000,
                "is_active": True,
                "created_at": now
            },
            {
                "id": wh2_id,
                "name": "North Distribution Center - Delhi",
                "code": "WH-DEL-01",
                "region": "North",
                "address": {
                    "street": "Sector 62, Logistics Hub",
                    "city": "New Delhi",
                    "state": "Delhi",
                    "zip": "110062",
                    "country": "India"
                },
                "manager_id": "",
                "capacity": 35000,
                "is_active": True,
                "created_at": now
            }
        ]

        for w in warehouses:
            try:
                cosmos_db.create_item(CONTAINER_WAREHOUSES, w)
                print(f"  ✅ Warehouse: {w['name']}")
            except Exception as e:
                print(f"  ⚠️  Warehouse {w['name']}: {e}")

        # ─────────────────────────────────────────
        # 3. PRODUCTS (2 items)
        # ─────────────────────────────────────────
        print("\n📱 Creating Products...")
        prod1_id = str(uuid.uuid4())
        prod2_id = str(uuid.uuid4())
        products = [
            {
                "id": prod1_id,
                "sku": "ELE-2607-LPTP",
                "name": "Dell Latitude 5540 Laptop",
                "description": "14-inch business laptop with Intel i7, 16GB RAM, 512GB SSD. Ideal for enterprise deployments.",
                "category": "Electronics",
                "subcategory": "Laptops",
                "barcode": "8901234567890",
                "barcode_image_url": "",
                "price": 1249.99,
                "cost_price": 899.00,
                "unit": "pcs",
                "weight": 1.8,
                "dimensions": {"length": 32, "width": 22, "height": 2},
                "image_url": "",
                "min_stock_level": 10,
                "reorder_point": 25,
                "reorder_quantity": 50,
                "max_stock_level": 200,
                "supplier_id": suppliers[0]["id"],
                "tags": ["laptop", "dell", "business"],
                "is_active": True,
                "created_at": now,
                "updated_at": now
            },
            {
                "id": prod2_id,
                "sku": "HOM-2607-ERGO",
                "name": "ErgoMax Pro Standing Desk",
                "description": "Electric height-adjustable standing desk with memory presets. 60x30 inch bamboo top.",
                "category": "Home & Garden",
                "subcategory": "Office Furniture",
                "barcode": "8901234567891",
                "barcode_image_url": "",
                "price": 549.00,
                "cost_price": 320.00,
                "unit": "pcs",
                "weight": 35.0,
                "dimensions": {"length": 152, "width": 76, "height": 125},
                "image_url": "",
                "min_stock_level": 5,
                "reorder_point": 10,
                "reorder_quantity": 20,
                "max_stock_level": 100,
                "supplier_id": suppliers[1]["id"],
                "tags": ["desk", "standing", "ergonomic"],
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }
        ]

        for p in products:
            try:
                cosmos_db.create_item(CONTAINER_PRODUCTS, p)
                print(f"  ✅ Product: {p['name']} (SKU: {p['sku']})")
            except Exception as e:
                print(f"  ⚠️  Product {p['name']}: {e}")

        # ─────────────────────────────────────────
        # 4. INVENTORY (2 items — one per product per warehouse)
        # ─────────────────────────────────────────
        print("\n📊 Creating Inventory Records...")
        inventory_items = [
            {
                "id": str(uuid.uuid4()),
                "product_id": prod1_id,
                "product_name": "Dell Latitude 5540 Laptop",
                "sku": "ELE-2607-LPTP",
                "warehouse_id": wh1_id,
                "warehouse_name": "Central Warehouse - Bangalore",
                "quantity": 150,
                "reserved_quantity": 12,
                "available_quantity": 138,
                "location": "Aisle A, Rack 3, Shelf 2",
                "batch_number": "BATCH-2026-001",
                "expiry_date": None,
                "last_counted": now,
                "last_updated": now
            },
            {
                "id": str(uuid.uuid4()),
                "product_id": prod2_id,
                "product_name": "ErgoMax Pro Standing Desk",
                "sku": "HOM-2607-ERGO",
                "warehouse_id": wh2_id,
                "warehouse_name": "North Distribution Center - Delhi",
                "quantity": 45,
                "reserved_quantity": 3,
                "available_quantity": 42,
                "location": "Zone B, Bay 7",
                "batch_number": "BATCH-2026-002",
                "expiry_date": None,
                "last_counted": now,
                "last_updated": now
            }
        ]

        for inv in inventory_items:
            try:
                cosmos_db.create_item(CONTAINER_INVENTORY, inv)
                print(f"  ✅ Inventory: {inv['product_name']} @ {inv['warehouse_name']} (Qty: {inv['quantity']})")
            except Exception as e:
                print(f"  ⚠️  Inventory {inv['product_name']}: {e}")

        # ─────────────────────────────────────────
        # 5. PURCHASE ORDERS (2 items)
        # ─────────────────────────────────────────
        print("\n🛒 Creating Purchase Orders...")
        purchase_orders = [
            {
                "id": str(uuid.uuid4()),
                "order_number": "PO-2026-00001",
                "supplier_id": suppliers[0]["id"],
                "supplier_name": "TechVision Electronics Ltd.",
                "status": "approved",
                "items": [
                    {
                        "product_id": prod1_id,
                        "product_name": "Dell Latitude 5540 Laptop",
                        "sku": "ELE-2607-LPTP",
                        "quantity": 50,
                        "received_quantity": 0,
                        "unit_price": 899.00,
                        "total": 44950.00
                    }
                ],
                "subtotal": 44950.00,
                "tax": 8091.00,
                "shipping": 500.00,
                "total_amount": 53541.00,
                "expected_delivery": (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d"),
                "warehouse_id": wh1_id,
                "notes": "Urgent order for Q3 enterprise client deployments.",
                "created_by": "demo-admin-id",
                "approved_by": "demo-admin-id",
                "created_at": now,
                "updated_at": now
            },
            {
                "id": str(uuid.uuid4()),
                "order_number": "PO-2026-00002",
                "supplier_id": suppliers[1]["id"],
                "supplier_name": "FurniCraft Industries",
                "status": "pending",
                "items": [
                    {
                        "product_id": prod2_id,
                        "product_name": "ErgoMax Pro Standing Desk",
                        "sku": "HOM-2607-ERGO",
                        "quantity": 20,
                        "received_quantity": 0,
                        "unit_price": 320.00,
                        "total": 6400.00
                    }
                ],
                "subtotal": 6400.00,
                "tax": 1152.00,
                "shipping": 1200.00,
                "total_amount": 8752.00,
                "expected_delivery": (datetime.now(timezone.utc) + timedelta(days=14)).strftime("%Y-%m-%d"),
                "warehouse_id": wh2_id,
                "notes": "Restocking for new office setup orders.",
                "created_by": "demo-admin-id",
                "approved_by": "",
                "created_at": now,
                "updated_at": now
            }
        ]

        for po in purchase_orders:
            try:
                cosmos_db.create_item(CONTAINER_PURCHASE_ORDERS, po)
                print(f"  ✅ Purchase Order: {po['order_number']} ({po['status']}) — ₹{po['total_amount']:,.2f}")
            except Exception as e:
                print(f"  ⚠️  PO {po['order_number']}: {e}")

        # ─────────────────────────────────────────
        # 6. SALES ORDERS (2 items)
        # ─────────────────────────────────────────
        print("\n💰 Creating Sales Orders...")
        sales_orders = [
            {
                "id": str(uuid.uuid4()),
                "order_number": "SO-2026-00001",
                "customer_name": "Infosys Technologies",
                "customer_email": "procurement@infosys.com",
                "customer_phone": "+91-9988776655",
                "channel": "ecommerce",
                "status": "confirmed",
                "items": [
                    {
                        "product_id": prod1_id,
                        "product_name": "Dell Latitude 5540 Laptop",
                        "sku": "ELE-2607-LPTP",
                        "quantity": 10,
                        "unit_price": 1249.99,
                        "discount": 500.00,
                        "total": 11999.90
                    }
                ],
                "subtotal": 11999.90,
                "tax": 2159.98,
                "discount": 500.00,
                "total_amount": 13659.88,
                "payment_status": "paid",
                "shipping_address": "44 Electronics City, Bangalore, Karnataka 560100",
                "notes": "Bulk order for new employee onboarding.",
                "created_by": "demo-admin-id",
                "created_at": now,
                "updated_at": now
            },
            {
                "id": str(uuid.uuid4()),
                "order_number": "SO-2026-00002",
                "customer_name": "WeWork India",
                "customer_email": "orders@wework.co.in",
                "customer_phone": "+91-8877665544",
                "channel": "manual",
                "status": "processing",
                "items": [
                    {
                        "product_id": prod2_id,
                        "product_name": "ErgoMax Pro Standing Desk",
                        "sku": "HOM-2607-ERGO",
                        "quantity": 5,
                        "unit_price": 549.00,
                        "discount": 0.00,
                        "total": 2745.00
                    }
                ],
                "subtotal": 2745.00,
                "tax": 494.10,
                "discount": 0.00,
                "total_amount": 3239.10,
                "payment_status": "pending",
                "shipping_address": "BKC Tower 3, Bandra, Mumbai, Maharashtra 400051",
                "notes": "Co-working space furniture refresh.",
                "created_by": "demo-admin-id",
                "created_at": now,
                "updated_at": now
            }
        ]

        for so in sales_orders:
            try:
                cosmos_db.create_item(CONTAINER_SALES_ORDERS, so)
                print(f"  ✅ Sales Order: {so['order_number']} → {so['customer_name']} ({so['status']})")
            except Exception as e:
                print(f"  ⚠️  SO {so['order_number']}: {e}")

        # ─────────────────────────────────────────
        # 7. NOTIFICATIONS (2 items)
        # ─────────────────────────────────────────
        print("\n🔔 Creating Notifications...")
        notifications = [
            {
                "id": str(uuid.uuid4()),
                "user_id": "demo-admin-id",
                "type": "low_stock",
                "severity": "warning",
                "title": "Low Stock Alert: ErgoMax Pro Standing Desk",
                "message": "Only 42 units remaining in North Distribution Center. Reorder point is 10 units.",
                "is_read": False,
                "entity_type": "product",
                "entity_id": prod2_id,
                "created_at": now
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": "demo-admin-id",
                "type": "order_update",
                "severity": "info",
                "title": "Purchase Order PO-2026-00001 Approved",
                "message": "Purchase order for 50 Dell Latitude 5540 Laptops has been approved. Expected delivery in 7 days.",
                "is_read": False,
                "entity_type": "purchase_order",
                "entity_id": purchase_orders[0]["id"],
                "created_at": now
            }
        ]

        for n in notifications:
            try:
                cosmos_db.create_item(CONTAINER_NOTIFICATIONS, n)
                print(f"  ✅ Notification: {n['title']}")
            except Exception as e:
                print(f"  ⚠️  Notification: {e}")

        # ─────────────────────────────────────────
        # DONE
        # ─────────────────────────────────────────
        print("\n" + "=" * 60)
        print("✅ SEEDING COMPLETE! All demo data has been saved to Azure Cosmos DB.")
        print("=" * 60)
        print("\nSummary:")
        print(f"  • 2 Suppliers")
        print(f"  • 2 Warehouses")
        print(f"  • 2 Products")
        print(f"  • 2 Inventory Records")
        print(f"  • 2 Purchase Orders")
        print(f"  • 2 Sales Orders")
        print(f"  • 2 Notifications")
        print(f"\n  Total: 14 documents created in Azure Cosmos DB")
        print(f"\n🎯 You can now add 1 more of each during your live demo!")
        print("=" * 60 + "\n")


if __name__ == '__main__':
    seed_data()
