"""
Tests for ETL schema validation module.
Tests Pydantic models and data validation functionality.
"""

import pytest
from datetime import datetime
from typing import Any, Dict, List
from pydantic import ValidationError

from etl.schema import (
    Listing,
    validate_listing,
    validate_batch,
    get_validation_stats
)


class TestListingModel:
    """Test the Listing Pydantic model."""
    
    def test_listing_minimal_valid(self):
        """Test creating listing with minimal required fields."""
        data: Dict[str, Any] = {
            "url": "https://example.com/listing/123"
        }
        listing = Listing(**data)
        assert listing.url == "https://example.com/listing/123"
        assert listing.currency == "EUR"  # Default value
    
    def test_listing_full_valid(self):
        """Test creating listing with all fields."""
        data: Dict[str, Any] = {
            "url": "https://example.com/listing/123",
            "title": "Beautiful Apartment",
            "description": "A lovely 2-bedroom apartment",
            "property_type": "apartment",
            "price": 150000.0,
            "currency": "EUR",
            "area": 75.0,
            "area_unit": "sqm",
            "area_sqm": 75.0,
            "address": "123 Main Street",
            "city": "Paris",
            "postal_code": "75001",
            "neighborhood": "Le Marais",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "rooms": 3,
            "bedrooms": 2,
            "bathrooms": 1,
            "floor": 2,
            "balcony": True,
            "parking": False,
            "garden": False,
            "elevator": True,
            "source": "test_scraper",
            "scraped_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        listing = Listing(**data)
        assert listing.title == "Beautiful Apartment"
        assert listing.price == 150000.0
        assert listing.latitude == 48.8566
        assert listing.rooms == 3
        assert listing.balcony is True
    
    def test_listing_validation_price_negative(self):
        """Test validation fails for negative price."""
        data = {
            "url": "https://example.com/listing/123",
            "price": -1000.0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            Listing(**data)
        
        assert "greater than or equal to 0" in str(exc_info.value)
    
    def test_listing_validation_price_too_high(self):
        """Test validation fails for extremely high price."""
        data = {
            "url": "https://example.com/listing/123",
            "price": 150000000.0  # 150 million - too high
        }
        
        with pytest.raises(ValidationError):
            Listing(**data)
    
    def test_listing_validation_area_invalid(self):
        """Test validation fails for invalid area."""
        data = {
            "url": "https://example.com/listing/123",
            "area_sqm": 0.5  # Too small
        }
        
        with pytest.raises(ValidationError):
            Listing(**data)
        
        data["area_sqm"] = 15000  # Too large
        with pytest.raises(ValidationError):
            Listing(**data)
    
    def test_listing_validation_coordinates(self):
        """Test coordinate validation."""
        # Invalid latitude
        data = {
            "url": "https://example.com/listing/123",
            "latitude": 91.0  # Too high
        }
        
        with pytest.raises(ValidationError):
            Listing(**data)
        
        # Invalid longitude
        data = {
            "url": "https://example.com/listing/123",
            "longitude": 181.0  # Too high
        }
        
        with pytest.raises(ValidationError):
            Listing(**data)
    
    def test_listing_validation_negative_rooms(self):
        """Test validation fails for negative room counts."""
        data = {
            "url": "https://example.com/listing/123",
            "rooms": -1
        }
        
        with pytest.raises(ValidationError):
            Listing(**data)
    
    def test_listing_validation_empty_url(self):
        """Test validation fails for empty URL."""
        data = {"url": ""}
        
        with pytest.raises(ValidationError):
            Listing(**data)
        
        data = {"url": "   "}
        
        with pytest.raises(ValidationError):
            Listing(**data)
    
    def test_listing_currency_normalization(self):
        """Test currency normalization in validation."""
        data = {
            "url": "https://example.com/listing/123",
            "currency": "usd"  # lowercase
        }
        
        listing = Listing(**data)
        assert listing.currency == "USD"  # Should normalize usd to USD
        
        # Test valid currencies
        for currency in ["EUR", "USD", "GBP", "CHF"]:
            data["currency"] = currency
            listing = Listing(**data)
            assert listing.currency == currency
    
    def test_listing_extra_fields_allowed(self):
        """Test that extra fields are allowed."""
        data = {
            "url": "https://example.com/listing/123",
            "custom_field": "custom_value",
            "another_field": 123
        }
        
        listing = Listing(**data)
        # Extra fields should be preserved
        assert hasattr(listing, 'custom_field')
        assert listing.custom_field == "custom_value"


class TestValidationFunctions:
    """Test validation helper functions."""
    
    def test_validate_listing_success(self):
        """Test successful listing validation."""
        data = {
            "url": "https://example.com/listing/123",
            "title": "Test Apartment",
            "price": 100000.0
        }
        
        result = validate_listing(data)
        assert result is not None
        assert isinstance(result, Listing)
        assert result.url == "https://example.com/listing/123"
        assert result.scraped_at is not None  # Should be auto-set
    
    def test_validate_listing_failure(self):
        """Test failed listing validation."""
        data = {
            "url": "",  # Invalid empty URL
            "price": -1000.0  # Invalid negative price
        }
        
        result = validate_listing(data)
        assert result is None
    
    def test_validate_listing_missing_scraped_at(self):
        """Test that scraped_at is auto-added if missing."""
        data = {
            "url": "https://example.com/listing/123"
        }
        
        result = validate_listing(data)
        assert result is not None
        assert result.scraped_at is not None
        assert isinstance(result.scraped_at, datetime)
    
    def test_validate_listing_exception_handling(self):
        """Test validation handles unexpected exceptions gracefully."""
        # Pass invalid data type that might cause unexpected errors
        result = validate_listing("not a dict")
        assert result is None
    
    def test_validate_batch_mixed_data(self):
        """Test batch validation with mixed valid/invalid data."""
        listings_data = [
            {
                "url": "https://example.com/1",
                "title": "Valid Listing 1",
                "price": 100000.0
            },
            {
                "url": "",  # Invalid - empty URL
                "price": 50000.0
            },
            {
                "url": "https://example.com/3",
                "title": "Valid Listing 3",
                "price": 200000.0
            },
            {
                "url": "https://example.com/4",
                "price": -1000.0  # Invalid - negative price
            }
        ]
        
        result = validate_batch(listings_data)
        
        # Should return only valid listings
        assert len(result) == 2
        assert all(isinstance(listing, Listing) for listing in result)
        assert result[0].url == "https://example.com/1"
        assert result[1].url == "https://example.com/3"
    
    def test_validate_batch_empty_list(self):
        """Test batch validation with empty list."""
        result = validate_batch([])
        assert result == []
    
    def test_validate_batch_all_valid(self):
        """Test batch validation with all valid listings."""
        listings_data = [
            {"url": f"https://example.com/{i}", "price": i * 1000.0}
            for i in range(1, 6)
        ]
        
        result = validate_batch(listings_data)
        assert len(result) == 5
        assert all(isinstance(listing, Listing) for listing in result)


class TestValidationStats:
    """Test validation statistics functionality."""
    
    def test_get_validation_stats_all_valid(self):
        """Test stats with all valid listings."""
        listings_data = [
            {"url": "https://example.com/1", "price": 100000.0},
            {"url": "https://example.com/2", "price": 150000.0}
        ]
        
        stats = get_validation_stats(listings_data)
        
        assert stats["total"] == 2
        assert stats["valid"] == 2
        assert stats["invalid"] == 0
        assert stats["validation_rate"] == 1.0
        assert len(stats["errors"]) == 0
    
    def test_get_validation_stats_mixed(self):
        """Test stats with mixed valid/invalid listings."""
        listings_data = [
            {"url": "https://example.com/1", "price": 100000.0},  # Valid
            {"url": "", "price": 50000.0},  # Invalid - empty URL
            {"url": "https://example.com/3", "price": 200000.0},  # Valid
            {"url": "https://example.com/4", "price": -1000.0}  # Invalid - negative price
        ]
        
        stats = get_validation_stats(listings_data)
        
        assert stats["total"] == 4
        assert stats["valid"] == 2
        assert stats["invalid"] == 2
        assert stats["validation_rate"] == 0.5
        assert len(stats["errors"]) == 2
        
        # Check error details
        error_urls = [error["url"] for error in stats["errors"]]
        assert "" in error_urls  # Empty URL stays empty  
        assert "https://example.com/4" in error_urls
    
    def test_get_validation_stats_all_invalid(self):
        """Test stats with all invalid listings."""
        listings_data = [
            {"url": "", "price": 100000.0},  # Invalid URL
            {"price": -1000.0}  # Missing URL and negative price
        ]
        
        stats = get_validation_stats(listings_data)
        
        assert stats["total"] == 2
        assert stats["valid"] == 0
        assert stats["invalid"] == 2
        assert stats["validation_rate"] == 0.0
        assert len(stats["errors"]) == 2
    
    def test_get_validation_stats_empty_list(self):
        """Test stats with empty list."""
        stats = get_validation_stats([])
        
        assert stats["total"] == 0
        assert stats["valid"] == 0
        assert stats["invalid"] == 0
        assert stats["validation_rate"] == 0
        assert len(stats["errors"]) == 0
    
    def test_get_validation_stats_error_limit(self):
        """Test that error list is limited to first 10 errors."""
        # Create 15 invalid listings
        listings_data = [
            {"url": "", "price": i * 1000.0}  # All invalid due to empty URL
            for i in range(15)
        ]
        
        stats = get_validation_stats(listings_data)
        
        assert stats["total"] == 15
        assert stats["invalid"] == 15
        assert len(stats["errors"]) == 10  # Should be limited to 10


class TestIntegrationScenarios:
    """Integration tests combining multiple validation scenarios."""
    
    def test_real_world_listing_validation(self):
        """Test validation with realistic listing data."""
        listing_data = {
            "url": "https://www.leboncoin.fr/ventes_immobilieres/123456",
            "title": "Appartement T3 avec balcon - Centre ville",
            "description": "Bel appartement de 75m² avec balcon, proche métro",
            "property_type": "apartment",
            "price": 185000.0,
            "currency": "EUR",
            "area": 75.0,
            "area_unit": "m²",
            "area_sqm": 75.0,
            "address": "15 Rue de la République, 69002 Lyon",
            "city": "Lyon",
            "postal_code": "69002",
            "latitude": 45.7640,
            "longitude": 4.8357,
            "rooms": 3,
            "bedrooms": 2,
            "bathrooms": 1,
            "floor": 3,
            "balcony": True,
            "parking": False,
            "elevator": True,
            "source": "leboncoin_scraper"
        }
        
        result = validate_listing(listing_data)
        
        assert result is not None
        assert isinstance(result, Listing)
        assert result.title == "Appartement T3 avec balcon - Centre ville"
        assert result.price == 185000.0
        assert result.area_sqm == 75.0
        assert result.latitude == 45.7640
        assert result.rooms == 3
        assert result.balcony is True
        assert result.scraped_at is not None
    
    def test_edge_cases_validation(self):
        """Test validation with various edge cases."""
        edge_cases = [
            # Minimum valid listing
            {"url": "https://example.com/1"},
            
            # With boundary values
            {
                "url": "https://example.com/2",
                "price": 0.01,  # Very small price
                "area_sqm": 1.0,  # Minimum area
                "latitude": -90.0,  # Minimum latitude
                "longitude": -180.0,  # Minimum longitude
                "rooms": 0,  # No rooms
                "floor": -5  # Basement
            },
            
            # With maximum values
            {
                "url": "https://example.com/3",
                "price": 99999999.0,  # High price (but under limit)
                "area_sqm": 9999.0,  # Large area (but under limit)
                "latitude": 90.0,  # Maximum latitude
                "longitude": 180.0  # Maximum longitude
            }
        ]
        
        results = validate_batch(edge_cases)
        
        # All should be valid
        assert len(results) == 3
        assert all(isinstance(result, Listing) for result in results)
