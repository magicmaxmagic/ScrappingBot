"""
Data validation and schema definitions for the ETL pipeline.
Provides Pydantic models for listing validation.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, ValidationError


class Listing(BaseModel):
    """
    Pydantic model for validated listing data.
    """
    # Basic information
    url: str = Field(..., description="Listing URL")
    title: Optional[str] = Field(None, description="Listing title")
    description: Optional[str] = Field(None, description="Property description")
    
    # Property details
    property_type: Optional[str] = Field(None, description="Type of property")
    price: Optional[float] = Field(None, ge=0, description="Price in local currency")
    currency: Optional[str] = Field("EUR", description="Currency code")
    
    # Area information
    area: Optional[float] = Field(None, ge=0, description="Property area")
    area_unit: Optional[str] = Field(None, description="Unit of area measurement")
    area_sqm: Optional[float] = Field(None, ge=0, description="Area in square meters")
    
    # Location
    address: Optional[str] = Field(None, description="Property address")
    city: Optional[str] = Field(None, description="City")
    postal_code: Optional[str] = Field(None, description="Postal code")
    neighborhood: Optional[str] = Field(None, description="Neighborhood")
    
    # Coordinates
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    
    # Property features
    rooms: Optional[int] = Field(None, ge=0, description="Number of rooms")
    bedrooms: Optional[int] = Field(None, ge=0, description="Number of bedrooms")
    bathrooms: Optional[int] = Field(None, ge=0, description="Number of bathrooms")
    floor: Optional[int] = Field(None, description="Floor number")
    
    # Additional features
    balcony: Optional[bool] = Field(None, description="Has balcony")
    parking: Optional[bool] = Field(None, description="Has parking")
    garden: Optional[bool] = Field(None, description="Has garden")
    elevator: Optional[bool] = Field(None, description="Has elevator")
    
    # Metadata
    source: Optional[str] = Field(None, description="Data source")
    scraped_at: Optional[datetime] = Field(None, description="When data was scraped")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    # Internal fields
    raw_html_path: Optional[str] = Field(None, description="Path to raw HTML file")
    listing_id: Optional[str] = Field(None, description="Internal listing ID")
    
    class Config:
        # Allow extra fields that might come from scrapers
        extra = "allow"
        # Use enum values instead of enum objects
        use_enum_values = True
        # JSON encoders for special types
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    @validator('price')
    def validate_price(cls, v):
        """Validate price is reasonable."""
        if v is not None and (v < 0 or v > 100000000):  # 100M max
            raise ValueError('Price must be between 0 and 100,000,000')
        return v
    
    @validator('area_sqm')
    def validate_area_sqm(cls, v):
        """Validate area is reasonable."""
        if v is not None and (v < 1 or v > 10000):  # 1-10000 sqm range
            raise ValueError('Area must be between 1 and 10,000 square meters')
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code."""
        if v is not None:
            v = v.upper().strip()
            valid_currencies = ['EUR', 'USD', 'GBP', 'CHF', 'CAD', 'AUD']
            if v not in valid_currencies:
                # Default to EUR for unknown currencies
                return 'EUR'
        return v
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL is not empty."""
        if not v or not v.strip():
            raise ValueError('URL is required and cannot be empty')
        return v.strip()


def validate_listing(data: Dict[str, Any]) -> Optional[Listing]:
    """
    Validate listing data against the Listing schema.
    
    Args:
        data: Dictionary containing listing data
        
    Returns:
        Validated Listing object or None if validation fails
    """
    try:
        # Set default scraped_at if not present
        if 'scraped_at' not in data or not data['scraped_at']:
            data['scraped_at'] = datetime.now()
        
        return Listing(**data)
    
    except ValidationError as e:
        # Log validation errors but don't fail completely
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Listing validation failed for URL {data.get('url', 'unknown')}: {e}")
        return None
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error validating listing: {e}")
        return None


def validate_batch(listings: List[Dict[str, Any]]) -> List[Listing]:
    """
    Validate a batch of listings.
    
    Args:
        listings: List of listing dictionaries
        
    Returns:
        List of validated Listing objects (invalid ones are filtered out)
    """
    validated = []
    
    for listing_data in listings:
        validated_listing = validate_listing(listing_data)
        if validated_listing:
            validated.append(validated_listing)
    
    return validated


def get_validation_stats(listings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get validation statistics for a batch of listings.
    
    Args:
        listings: List of listing dictionaries
        
    Returns:
        Dictionary with validation statistics
    """
    total = len(listings)
    valid = 0
    invalid = 0
    errors = []
    
    for listing_data in listings:
        try:
            Listing(**listing_data)
            valid += 1
        except ValidationError as e:
            invalid += 1
            errors.append({
                'url': listing_data.get('url', 'unknown'),
                'errors': [str(err) for err in e.errors()]
            })
        except Exception as e:
            invalid += 1
            errors.append({
                'url': listing_data.get('url', 'unknown'),
                'errors': [str(e)]
            })
    
    return {
        'total': total,
        'valid': valid,
        'invalid': invalid,
        'validation_rate': valid / total if total > 0 else 0,
        'errors': errors[:10]  # Limit to first 10 errors
    }
