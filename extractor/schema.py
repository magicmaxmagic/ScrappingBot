from __future__ import annotations

from datetime import datetime
from typing import Optional, Annotated

from pydantic import BaseModel, Field, ValidationError, field_validator, AnyUrl, UrlConstraints


FileOrHttpUrl = Annotated[AnyUrl, UrlConstraints(allowed_schemes=["http", "https", "file"])]


class Listing(BaseModel):
    # Required by spec
    kind: str = Field(description="Type of listing: 'sale' or 'rent'")
    price: float = Field(ge=0, description="Price amount numeric")
    currency: str = Field(pattern=r"^[A-Z]{3}$", description="ISO currency code, e.g. EUR, USD")
    url: FileOrHttpUrl = Field(description="Canonical URL of the listing (http/https, allows file:// in local tests)")

    # Optional additional fields
    title: Optional[str] = None
    address: Optional[str] = None
    area_sqm: Optional[float] = Field(default=None, ge=0, description="Surface in m²")
    rooms: Optional[float] = Field(default=None, ge=0)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    neighborhood: Optional[str] = None

    site_domain: Optional[str] = None
    raw_html_path: Optional[str] = None

    extracted_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in {"sale", "rent"}:
            raise ValueError("kind must be 'sale' or 'rent'")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = (v or "").strip().upper()
        if len(v) != 3:
            raise ValueError("currency must be a 3-letter ISO code")
        return v


def get_extraction_json_schema() -> dict:
    # Minimal JSON Schema emphasizing required properties
    return Listing.model_json_schema()


def validate_listing(data: dict) -> Listing:
    try:
        return Listing.model_validate(data)
    except ValidationError as e:
        raise
