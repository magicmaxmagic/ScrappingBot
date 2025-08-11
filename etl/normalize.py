from __future__ import annotations

from typing import Optional

FT2_TO_M2 = 0.092903


def to_sqm(area_value: Optional[float], unit: Optional[str]) -> Optional[float]:
    if area_value is None:
        return None
    unit = (unit or "").strip().lower()
    if unit in {"m2", "sqm", "m²"}:
        return float(area_value)
    if unit in {"ft2", "ft^2", "sqft", "ft²"}:
        return float(area_value) * FT2_TO_M2
    # Unknown unit; return as-is (could be handled upstream)
    return float(area_value)


def normalize_currency(cur: Optional[str]) -> Optional[str]:
    if not cur:
        return None
    cur = cur.strip().upper()
    if cur == "€":
        return "EUR"
    if cur == "$":
        return "USD"
    return cur
