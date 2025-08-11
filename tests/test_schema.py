from extractor.schema import Listing, validate_listing
import pytest


def test_listing_validation_minimal():
    data = {
        "kind": "sale",
        "price": 100000.0,
        "currency": "EUR",
        "url": "https://example.com/listing/123",
    }
    l = validate_listing(data)
    assert isinstance(l, Listing)


def test_listing_validation_kind_error():
    data = {
        "kind": "other",
        "price": 100000.0,
        "currency": "EUR",
        "url": "https://example.com/listing/123",
    }
    with pytest.raises(Exception):
        validate_listing(data)
