"""Seed 2 demo users into the database."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app
from app.services.cosmos_db_service import cosmos_db
from app.models.user import User
from app.utils.constants import CONTAINER_USERS
from datetime import datetime, timezone

app = create_app()
with app.app_context():
    now = datetime.now(timezone.utc).isoformat()

    # Create Admin user
    admin = User(
        id="demo-admin-id",
        email="admin@inventory.com",
        first_name="System",
        last_name="Administrator",
        role="admin",
        phone="+91-9900001111",
        is_active=True,
        last_login=now,
        created_at=now,
        updated_at=now
    )
    admin.set_password("Admin@123")

    # Create Manager user
    manager = User(
        email="manager@inventory.com",
        first_name="Priya",
        last_name="Mehta",
        role="manager",
        phone="+91-9900002222",
        is_active=True,
        created_at=now,
        updated_at=now
    )
    manager.set_password("Manager@123")

    for user in [admin, manager]:
        try:
            cosmos_db.create_item(CONTAINER_USERS, user.to_dict())
            print(f"Created user: {user.email} ({user.role})")
        except Exception as e:
            print(f"User {user.email}: {e}")

    print("Done!")
