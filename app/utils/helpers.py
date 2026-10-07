"""
General helper functions.
"""

import uuid
from datetime import datetime, timezone


def generate_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


def get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def format_currency(amount, symbol='$') -> str:
    """Format a number as currency."""
    try:
        return f"{symbol}{float(amount):,.2f}"
    except (ValueError, TypeError):
        return f"{symbol}0.00"


def format_date(date_str: str, fmt: str = '%b %d, %Y') -> str:
    """Format ISO date string to readable format."""
    if not date_str:
        return ''
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime(fmt)
    except (ValueError, AttributeError):
        return date_str


def format_datetime(date_str: str) -> str:
    """Format ISO date to readable datetime."""
    return format_date(date_str, '%b %d, %Y %I:%M %p')


def paginate_list(items: list, page: int, per_page: int) -> tuple:
    """Paginate a list of items. Returns (paginated_items, pagination_info)."""
    page = max(1, page)
    per_page = max(1, min(per_page, 100))
    total = len(items)
    total_pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = items[start:end]
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < total_pages else None
    }
    return paginated, pagination


def safe_int(value, default: int = 0) -> int:
    """Safely convert a value to int."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def generate_order_number(prefix: str, counter: int) -> str:
    """Generate formatted order number like PO-2026-00001."""
    year = datetime.now(timezone.utc).strftime('%Y')
    return f"{prefix}-{year}-{counter:05d}"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values."""
    if old_value == 0:
        return 100.0 if new_value > 0 else 0.0
    return round(((new_value - old_value) / abs(old_value)) * 100, 2)


def truncate_string(text: str, length: int = 50) -> str:
    """Truncate string with ellipsis."""
    if not text or len(text) <= length:
        return text or ''
    return text[:length] + '...'
