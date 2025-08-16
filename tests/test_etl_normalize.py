"""
Tests for ETL normalization module.
Tests currency normalization, area conversion, and price cleaning.
"""

import pytest
import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from typing import Optional

from etl.normalize import (
    normalize_currency,
    to_sqm, 
    to_square_meters,
    convert,
    normalize_price,
    normalize_address
)


class TestCurrencyNormalization:
    """Test currency normalization functionality."""
    
    def test_normalize_currency_symbols(self):
        """Test normalization of currency symbols."""
        assert normalize_currency("€") == "EUR"
        assert normalize_currency("$") == "USD"
        assert normalize_currency("£") == "GBP"
    
    def test_normalize_currency_words(self):
        """Test normalization of currency words."""
        assert normalize_currency("euro") == "EUR"
        assert normalize_currency("EUROS") == "EUR"
        assert normalize_currency("dollar") == "USD"
        assert normalize_currency("pound") == "GBP"
    
    def test_normalize_currency_codes(self):
        """Test direct currency codes."""
        assert normalize_currency("EUR") == "EUR"
        assert normalize_currency("USD") == "USD"
        assert normalize_currency("CHF") == "CHF"
    
    def test_normalize_currency_none_or_empty(self):
        """Test handling of None or empty values."""
        assert normalize_currency(None) == "EUR"
        assert normalize_currency("") == "EUR"
        assert normalize_currency("   ") == "EUR"
    
    def test_normalize_currency_unknown(self):
        """Test handling of unknown currencies."""
        assert normalize_currency("UNKNOWN") == "EUR"
        assert normalize_currency("XYZ") == "EUR"


class TestAreaConversion:
    """Test area conversion utilities."""
    
    def test_to_sqm_square_meters(self):
        """Test conversion from square meters (should remain unchanged)."""
        assert to_sqm(100, "sqm") == 100
        assert to_sqm(50.5, "m²") == 50.5
        assert to_sqm(25, "m2") == 25
    
    def test_to_sqm_square_feet(self):
        """Test conversion from square feet to square meters."""
        result = to_sqm(100, "sqft")
        assert result is not None
        assert abs(result - 9.29) < 0.01  # 100 sq ft ≈ 9.29 sq m
    
    def test_to_sqm_acres(self):
        """Test conversion from acres to square meters."""
        result = to_sqm(1, "acres")
        assert result is not None
        assert abs(result - 4046.86) < 0.01
    
    def test_to_sqm_hectares(self):
        """Test conversion from hectares to square meters."""
        result = to_sqm(1, "hectares")
        assert result is not None
        assert result == 10000.0
    
    def test_to_sqm_invalid_input(self):
        """Test handling of invalid input."""
        assert to_sqm(None, "sqm") is None
        assert to_sqm(100, None) is None
        # Test with non-numeric string
        with patch('builtins.float', side_effect=ValueError):
            assert to_sqm(100, "sqm") is None
    
    def test_to_sqm_unknown_unit(self):
        """Test handling of unknown units (should assume square meters)."""
        assert to_sqm(100, "unknown") == 100
    
    def test_to_square_meters_alias(self):
        """Test the to_square_meters alias function."""
        assert to_square_meters(100, "sqft") == to_sqm(100, "sqft")
    
    def test_convert_alias(self):
        """Test the convert alias function."""
        assert convert(100, "sqft") == to_sqm(100, "sqft")


class TestPriceNormalization:
    """Test price normalization functionality."""
    
    def test_normalize_price_basic(self):
        """Test basic price normalization."""
        assert normalize_price("100000") == 100000.0
        assert normalize_price("1,000,000") == 1000000.0
        assert normalize_price("1.500.000") == 1500000.0
    
    def test_normalize_price_with_currency(self):
        """Test price with currency symbols."""
        assert normalize_price("€100,000") == 100000.0
        assert normalize_price("$250,000") == 250000.0
        assert normalize_price("£180,000") == 180000.0
    
    def test_normalize_price_decimal(self):
        """Test decimal prices."""
        assert normalize_price("99,999.50") == 99999.5
        assert normalize_price("1,234.56") == 1234.56
    
    def test_normalize_price_european_format(self):
        """Test European number format."""
        assert normalize_price("1.234,56") == 1234.56
        assert normalize_price("999.999,00") == 999999.0
    
    def test_normalize_price_invalid(self):
        """Test invalid price inputs."""
        assert normalize_price(None) is None
        assert normalize_price("") is None
        assert normalize_price("not_a_price") is None
        # The function extracts numbers from text, so abc123def -> 123.0 is expected
        assert normalize_price("abc123def") == 123.0


class TestAddressNormalization:
    """Test address normalization functionality."""
    
    def test_normalize_address_basic(self):
        """Test basic address normalization."""
        assert normalize_address("123 main street") == "123 Main Street"
        assert normalize_address("PARIS   FRANCE") == "Paris France"
    
    def test_normalize_address_whitespace(self):
        """Test whitespace handling."""
        assert normalize_address("  123   main   street  ") == "123 Main Street"
        assert normalize_address("\n\t 456 elm st \r\n") == "456 Elm St"
    
    def test_normalize_address_none_or_empty(self):
        """Test None or empty addresses."""
        assert normalize_address(None) is None
        assert normalize_address("") is None
        assert normalize_address("   ") is None


class TestIntegrationScenarios:
    """Integration tests combining multiple normalization functions."""
    
    def test_complete_listing_normalization(self):
        """Test normalizing a complete listing."""
        raw_listing = {
            "price": "€250,000.50",
            "currency": "euros",
            "area": "85.5",
            "area_unit": "m²",
            "address": "  123   rue   de   rivoli   paris  "
        }
        
        # Normalize all fields
        normalized = {
            "price": normalize_price(raw_listing["price"]),
            "currency": normalize_currency(raw_listing["currency"]),
            "area_sqm": to_sqm(float(raw_listing["area"]), raw_listing["area_unit"]),
            "address": normalize_address(raw_listing["address"])
        }
        
        assert normalized["price"] == 250000.5
        assert normalized["currency"] == "EUR"
        assert normalized["area_sqm"] == 85.5
        assert normalized["address"] == "123 Rue De Rivoli Paris"
    
    def test_edge_cases_combination(self):
        """Test combination of edge cases."""
        # All None values
        assert normalize_currency(None) == "EUR"
        assert to_sqm(None, None) is None
        assert normalize_price(None) is None
        assert normalize_address(None) is None
        
        # Empty strings
        assert normalize_currency("") == "EUR"
        assert normalize_price("") is None
        assert normalize_address("") is None
