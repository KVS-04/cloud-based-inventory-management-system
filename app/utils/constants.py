"""
Application-wide constants.
"""

# --- User Roles ---
USER_ROLES = ['admin', 'manager', 'staff']

# --- Product ---
PRODUCT_UNITS = ['pcs', 'kg', 'litre', 'box', 'pack', 'meter', 'set']
PRODUCT_CATEGORIES = [
    'Electronics', 'Clothing', 'Food & Beverage', 'Home & Garden',
    'Sports', 'Books', 'Toys', 'Health & Beauty', 'Automotive', 'Office Supplies'
]

# --- Order Statuses ---
PO_STATUSES = ['draft', 'pending', 'approved', 'received', 'partial', 'cancelled']
SO_STATUSES = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
RETURN_STATUSES = ['pending', 'approved', 'received', 'processed', 'rejected']
PAYMENT_STATUSES = ['pending', 'paid', 'refunded']

# --- Inventory ---
MOVEMENT_TYPES = ['stock_in', 'stock_out', 'transfer', 'adjustment', 'return']
REFERENCE_TYPES = ['purchase_order', 'sales_order', 'return', 'manual', 'system']
STOCK_STATUSES = ['out_of_stock', 'critical', 'low', 'normal']

# --- Channels ---
CHANNELS = ['pos', 'ecommerce', 'warehouse', 'manual']

# --- Supplier ---
PAYMENT_TERMS = ['Net 15', 'Net 30', 'Net 45', 'Net 60', 'COD', 'Prepaid']

# --- Notifications ---
NOTIFICATION_TYPES = ['low_stock', 'reorder', 'order_update', 'system', 'alert']
SEVERITIES = ['info', 'warning', 'critical']

# --- Audit ---
AUDIT_ACTIONS = ['create', 'update', 'delete', 'login', 'logout', 'export', 'approve', 'receive', 'cancel']
ENTITY_TYPES = [
    'product', 'inventory', 'purchase_order', 'sales_order',
    'return', 'user', 'supplier', 'warehouse', 'notification'
]

# --- Return Reasons ---
RETURN_REASONS = ['defective', 'wrong_item', 'damaged', 'not_needed', 'expired', 'other']
RETURN_CONDITIONS = ['new', 'used', 'damaged']

# --- Cosmos DB Container Names ---
CONTAINER_USERS = 'users'
CONTAINER_PRODUCTS = 'products'
CONTAINER_INVENTORY = 'inventory'
CONTAINER_MOVEMENTS = 'inventory_movements'
CONTAINER_PURCHASE_ORDERS = 'purchase_orders'
CONTAINER_SALES_ORDERS = 'sales_orders'
CONTAINER_RETURNS = 'returns'
CONTAINER_SUPPLIERS = 'suppliers'
CONTAINER_WAREHOUSES = 'warehouses'
CONTAINER_NOTIFICATIONS = 'notifications'
CONTAINER_AUDIT_LOGS = 'audit_logs'

# --- Container Partition Keys ---
PARTITION_KEYS = {
    CONTAINER_USERS: '/role',
    CONTAINER_PRODUCTS: '/category',
    CONTAINER_INVENTORY: '/warehouse_id',
    CONTAINER_MOVEMENTS: '/product_id',
    CONTAINER_PURCHASE_ORDERS: '/status',
    CONTAINER_SALES_ORDERS: '/status',
    CONTAINER_RETURNS: '/return_type',
    CONTAINER_SUPPLIERS: '/category',
    CONTAINER_WAREHOUSES: '/region',
    CONTAINER_NOTIFICATIONS: '/user_id',
    CONTAINER_AUDIT_LOGS: '/entity_type',
}

# --- Report Types ---
REPORT_TYPES = [
    'inventory_summary', 'sales_report', 'purchase_report',
    'stock_movement', 'low_stock', 'demand_forecast'
]

# --- Pagination Defaults ---
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 25
MAX_PER_PAGE = 100
