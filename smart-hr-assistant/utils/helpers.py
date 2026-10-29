"""
Helper utilities for data persistence, file paths, and formatting.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR_NAME = os.getenv("DATA_DIR", "data")
DATA_DIR = BASE_DIR / DATA_DIR_NAME
DEFAULT_EMPLOYEE_ID = os.getenv("DEFAULT_EMPLOYEE_ID", "EMP-001")


def get_data_path(filename: str) -> Path:
    """Return the absolute path for a file inside the data directory."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / filename


def load_json(filename: str, default: Optional[Any] = None) -> Any:
    """Safely load a JSON file from the data directory.

    Args:
        filename: Name of the JSON file (e.g. 'employees.json')
        default: Fallback object if file does not exist or fails to parse.

    Returns:
        Parsed JSON object or default.
    """
    path = get_data_path(filename)
    if not path.exists():
        return default if default is not None else []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Warning] Error reading {filename}: {e}")
        return default if default is not None else []


def save_json(filename: str, data: Any) -> bool:
    """Save data to a JSON file in the data directory.

    Args:
        filename: Name of the JSON file (e.g. 'leave_requests.json')
        data: Data to be serialized.

    Returns:
        True if successfully saved, False otherwise.
    """
    path = get_data_path(filename)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[Error] Failed to save {filename}: {e}")
        return False


def get_current_employee_id() -> str:
    """Return the active default employee ID."""
    return DEFAULT_EMPLOYEE_ID


def format_date(date_str: str) -> str:
    """Format ISO date YYYY-MM-DD into DD.MM.YYYY."""
    try:
        parts = date_str.split("-")
        if len(parts) == 3:
            return f"{parts[2]}.{parts[1]}.{parts[0]}"
    except Exception:
        pass
    return date_str


def format_currency(amount: float, currency: str = "TL") -> str:
    """Format number as currency string."""
    return f"{amount:,.2f} {currency}".replace(",", ".")
