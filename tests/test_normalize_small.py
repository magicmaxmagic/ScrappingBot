import pytest
from etl.normalize import normalize_currency, to_sqm, normalize_price, normalize_address


def test_normalize_currency_basic():
    assert normalize_currency('€') == 'EUR'
    assert normalize_currency('usd') == 'USD'
    assert normalize_currency(None) == 'EUR'


def test_to_sqm_conversions():
    assert to_sqm(100, 'sqm') == 100
    assert to_sqm(10, 'sqft') == pytest.approx(0.93, rel=1e-2)
    assert to_sqm(None, 'sqm') is None


def test_normalize_price_formats():
    assert normalize_price('€1,200') == 1200
    assert normalize_price('1.234,56') == 1234.56
    assert normalize_price('bad') is None


def test_normalize_address():
    assert normalize_address('  123 main st  ') == '123 Main St'
    assert normalize_address(None) is None
