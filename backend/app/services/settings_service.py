"""Runtime-editable store settings backed by the store_settings table.

Falls back to .env defaults when a key has not been configured yet.
"""

from typing import Any, Dict

from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.models import StoreSetting
from app.utils.exceptions import ValidationError

# key -> (default value, validator)
_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "store_name": {"default": "ShelfSpace", "type": "str", "min": 1, "max": 80},
    "support_email": {"default": "support@shelfspace.local", "type": "email"},
    "currency": {"default": app_settings.DEFAULT_CURRENCY, "type": "str", "min": 1, "max": 8},
    "tax_percent": {"default": app_settings.DEFAULT_TAX_PERCENT, "type": "float", "min": 0, "max": 100},
    "shipping_fee": {"default": app_settings.DEFAULT_SHIPPING_FEE, "type": "float", "min": 0, "max": 100000},
    "free_shipping_threshold": {
        "default": app_settings.DEFAULT_FREE_SHIPPING_THRESHOLD,
        "type": "float",
        "min": 0,
        "max": 1000000,
    },
    "return_window_days": {
        "default": app_settings.DEFAULT_RETURN_WINDOW_DAYS,
        "type": "int",
        "min": 0,
        "max": 365,
    },
    "low_stock_threshold": {
        "default": app_settings.DEFAULT_LOW_STOCK_THRESHOLD,
        "type": "int",
        "min": 0,
        "max": 1000,
    },
}


def get_setting(db: Session, key: str) -> Any:
    definition = _DEFINITIONS.get(key)
    if definition is None:
        raise KeyError(f"Unknown setting: {key}")
    row = db.get(StoreSetting, key)
    return row.value if row is not None else definition["default"]


def get_int(db: Session, key: str) -> int:
    return int(get_setting(db, key))


def get_float(db: Session, key: str) -> float:
    return float(get_setting(db, key))


def get_str(db: Session, key: str) -> str:
    return str(get_setting(db, key))


def all_settings(db: Session) -> Dict[str, Any]:
    return {key: get_setting(db, key) for key in _DEFINITIONS}


def update_settings(db: Session, updates: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in updates.items():
        if key not in _DEFINITIONS:
            raise ValidationError(f"Unknown setting: {key}")
        _validate(key, value)
        row = db.get(StoreSetting, key)
        if row is None:
            row = StoreSetting(key=key, value=value)
            db.add(row)
        else:
            row.value = value
    db.flush()
    return all_settings(db)


def _validate(key: str, value: Any) -> None:
    definition = _DEFINITIONS[key]
    vtype = definition["type"]
    if vtype == "str":
        if not isinstance(value, str) or len(value) < definition.get("min", 0) or len(value) > definition.get("max", 255):
            raise ValidationError(f"Invalid value for {key}.")
    elif vtype == "email":
        if not isinstance(value, str) or "@" not in value:
            raise ValidationError(f"Invalid value for {key}: expected an email address.")
    elif vtype in ("float", "int"):
        try:
            num = float(value)
        except (TypeError, ValueError):
            raise ValidationError(f"Invalid value for {key}: expected a number.")
        if num < definition["min"] or num > definition["max"]:
            raise ValidationError(f"{key} must be between {definition['min']} and {definition['max']}.")
