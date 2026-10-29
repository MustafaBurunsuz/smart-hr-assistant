"""
Input validation functions for Smart HR Assistant.
"""

import re
from datetime import datetime
from typing import Optional, Tuple


def validate_employee_id(employee_id: str) -> bool:
    """Check if employee ID matches standard format (e.g., EMP-001).

    Args:
        employee_id: String representing employee ID.

    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(employee_id, str):
        return False
    return bool(re.match(r"^EMP-\d{3,5}$", employee_id.strip().upper()))


def validate_date_string(date_str: str) -> Tuple[bool, Optional[str]]:
    """Validate and normalize a date string into YYYY-MM-DD.

    Supports formats:
    - YYYY-MM-DD
    - DD.MM.YYYY
    - DD/MM/YYYY

    Args:
        date_str: Raw input date.

    Returns:
        Tuple of (is_valid, normalized_date_str)
    """
    if not date_str:
        return False, None

    date_str = date_str.strip()
    formats = ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return True, dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return False, None


def validate_positive_integer(value: any) -> Tuple[bool, int]:
    """Validate that value is a positive integer > 0."""
    try:
        val = int(value)
        if val > 0:
            return True, val
        return False, 0
    except (ValueError, TypeError):
        return False, 0
