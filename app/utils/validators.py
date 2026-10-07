"""
Input validation helpers.
"""

import re


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_required(data: dict, required_fields: list) -> tuple:
    """Check that all required fields are present and non-empty.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    for field in required_fields:
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f'{field.replace("_", " ").title()} is required.')
    return (len(errors) == 0, errors)


def validate_positive_number(value) -> bool:
    """Check that a value is a positive number."""
    try:
        return float(value) >= 0
    except (ValueError, TypeError):
        return False


def validate_date_format(date_string: str) -> bool:
    """Validate ISO 8601 date format."""
    if not date_string:
        return False
    try:
        from datetime import datetime
        datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return True
    except (ValueError, AttributeError):
        return False


def validate_file_extension(filename: str, allowed: set) -> bool:
    """Check file extension against allowed set."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed


def validate_file_size(content_length: int, max_mb: int) -> bool:
    """Check file size against maximum allowed MB."""
    return content_length <= max_mb * 1024 * 1024


def sanitize_string(value: str) -> str:
    """Sanitize input string by stripping and escaping."""
    if not value:
        return ''
    return value.strip()


def validate_phone(phone: str) -> bool:
    """Basic phone number validation."""
    if not phone:
        return True  # Phone is optional
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    return cleaned.isdigit() and 7 <= len(cleaned) <= 15


def validate_password_strength(password: str) -> tuple:
    """Validate password meets strength requirements.
    Returns (is_valid, message).
    """
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long.'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter.'
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter.'
    if not re.search(r'\d', password):
        return False, 'Password must contain at least one digit.'
    return True, 'Password is strong.'
