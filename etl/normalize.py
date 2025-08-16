"""
Data normalization utilities for the ETL pipeline.
Handles currency and area unit conversions.
"""

import re
from typing import Optional


def normalize_currency(currency: Optional[str]) -> str:
    """
    Normalize currency strings to standardized codes.
    
    Args:
        currency: Raw currency string from scraped data
        
    Returns:
        Standardized currency code
    """
    if not currency:
        return "EUR"
    
    currency = str(currency).upper().strip()
    
    # Common currency mappings
    currency_map = {
        "€": "EUR",
        "EUR": "EUR",
        "EURO": "EUR",
        "EUROS": "EUR",
        "$": "USD",
        "USD": "USD",
        "DOLLAR": "USD",
        "DOLLARS": "USD",
        "£": "GBP",
        "GBP": "GBP",
        "POUND": "GBP",
        "POUNDS": "GBP",
        "CHF": "CHF",
        "FRANC": "CHF",
        "FRANCS": "CHF",
    }
    
    # Direct mapping
    if currency in currency_map:
        return currency_map[currency]
    
    # Extract currency code from text
    for key, value in currency_map.items():
        if key in currency:
            return value
    
    # Default fallback
    return "EUR"


def to_sqm(area: Optional[float], area_unit: Optional[str]) -> Optional[float]:
    """
    Convert area to square meters.
    
    Args:
        area: Numeric area value
        area_unit: Unit of the area (sqm, sqft, etc.)
        
    Returns:
        Area in square meters, or None if conversion not possible
    """
    if not area or not area_unit:
        return None
    
    try:
        area_value = float(area)
    except (ValueError, TypeError):
        return None
    
    unit = str(area_unit).lower().strip()
    
    # Conversion factors to square meters
    conversions = {
        "sqm": 1.0,
        "m²": 1.0,
        "m2": 1.0,
        "square meters": 1.0,
        "square metres": 1.0,
        "sqft": 0.092903,  # Square feet to square meters
        "ft²": 0.092903,
        "ft2": 0.092903,
        "square feet": 0.092903,
        "acres": 4046.86,  # Acres to square meters
        "hectares": 10000.0,  # Hectares to square meters
        "ha": 10000.0,
    }
    
    # Find matching conversion
    for key, factor in conversions.items():
        if key in unit:
            return round(area_value * factor, 2)
    
    # If no specific unit found, assume square meters
    return area_value


def to_square_meters(area: Optional[float], area_unit: Optional[str]) -> Optional[float]:
    """Alias for to_sqm for backward compatibility."""
    return to_sqm(area, area_unit)


def convert(area: Optional[float], area_unit: Optional[str]) -> Optional[float]:
    """Alias for to_sqm for backward compatibility."""
    return to_sqm(area, area_unit)


def normalize_price(price: Optional[str]) -> Optional[float]:
    """
    Normalize price strings to numeric values.
    
    Args:
        price: Raw price string from scraped data
        
    Returns:
        Numeric price value or None
    """
    if not price:
        return None
    
    # Convert to string and clean
    price_str = str(price).strip()
    
    # Remove currency symbols and common formatting
    price_str = re.sub(r'[€$£¥₹₽₴₪₩₦₡₨₹₪₩₦₡₨]', '', price_str)
    price_str = re.sub(r'[^\d.,\-]', '', price_str)
    
    if not price_str:
        return None
    
    # Handle different decimal separators
    if ',' in price_str and '.' in price_str:
        # Both present - determine format based on position
        last_comma = price_str.rfind(',')
        last_dot = price_str.rfind('.')
        
        if last_comma > last_dot:
            # European format: 1.234.567,89
            price_str = price_str.replace('.', '').replace(',', '.')
        else:
            # US format: 1,234,567.89
            price_str = re.sub(r',(?=\d{3})', '', price_str)  # Remove thousand separators only
    elif ',' in price_str:
        # Only comma - could be thousands sep or decimal
        parts = price_str.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Likely decimal separator (1234,56)
            price_str = price_str.replace(',', '.')
        else:
            # Likely thousands separator (1,234,567)
            price_str = price_str.replace(',', '')
    elif '.' in price_str:
        # Only dots - could be European thousands or decimal
        parts = price_str.split('.')
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Likely decimal (1234.56)
            pass  # Keep as is
        elif len(parts) > 2:
            # Multiple dots - European thousands (1.234.567)
            price_str = price_str.replace('.', '')
        else:
            # Single dot with >2 decimals - likely thousands
            if len(parts[1]) > 2:
                price_str = price_str.replace('.', '')
    
    try:
        return float(price_str)
    except (ValueError, TypeError):
        return None


def normalize_address(address: Optional[str]) -> Optional[str]:
    """
    Normalize address strings for consistency.
    
    Args:
        address: Raw address string
        
    Returns:
        Cleaned address string
    """
    if not address:
        return None
    
    # Basic cleaning
    address = str(address).strip()
    
    # Remove extra whitespace
    address = re.sub(r'\s+', ' ', address)
    
    # Capitalize properly
    address = address.title()
    
    return address if address else None
