"""
Pytest configuration and fixtures for ScrappingBot tests.
Sets up test environment and shared fixtures.
"""

import os
import sys
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Ensure project root is on sys.path for imports like `etl`
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)


# Pytest markers configuration
pytest_markers = [
    "integration: marks tests as integration tests (may be slow)",
    "slow: marks tests as slow running",
    "performance: marks tests as performance tests",
    "requires_docker: marks tests that require Docker",
    "requires_database: marks tests that require database connection",
    "requires_network: marks tests that require network access"
]


@pytest.fixture(scope="session")
def project_root():
    """Fixture providing project root directory."""
    return Path(ROOT)


@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """Fixture providing test data directory."""
    test_data_path = project_root / "tests" / "data"
    test_data_path.mkdir(exist_ok=True)
    return test_data_path


@pytest.fixture
def sample_listing_data():
    """Fixture providing sample listing data for tests."""
    return {
        "url": "https://example.com/listing/123",
        "title": "Beautiful Test Apartment",
        "description": "A lovely 2-bedroom apartment for testing",
        "property_type": "apartment",
        "price": 150000.0,
        "currency": "EUR",
        "area": 75.0,
        "area_unit": "sqm",
        "area_sqm": 75.0,
        "address": "123 Test Street, Test City",
        "city": "Test City",
        "postal_code": "12345",
        "rooms": 3,
        "bedrooms": 2,
        "bathrooms": 1,
        "balcony": True,
        "parking": False,
        "source": "test_scraper"
    }


@pytest.fixture
def sample_listing_batch():
    """Fixture providing a batch of sample listings for tests."""
    return [
        {
            "url": "https://example.com/listing/1",
            "title": "Apartment 1",
            "price": 100000.0,
            "area_sqm": 50.0
        },
        {
            "url": "https://example.com/listing/2", 
            "title": "House 1",
            "price": 250000.0,
            "area_sqm": 120.0
        },
        {
            "url": "https://example.com/listing/3",
            "title": "Studio 1", 
            "price": 80000.0,
            "area_sqm": 30.0
        }
    ]


@pytest.fixture
def temp_json_file():
    """Fixture providing temporary JSON file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    yield Path(temp_path)
    
    # Cleanup
    if Path(temp_path).exists():
        os.unlink(temp_path)


@pytest.fixture
def mock_database_connection():
    """Fixture providing mock database connection for tests."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (1,)
    mock_cursor.fetchall.return_value = [(1, "test")]
    
    return mock_conn


@pytest.fixture
def mock_http_response():
    """Fixture providing mock HTTP response for scraper tests."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '''
    <html>
    <body>
        <div class="listing">
            <h1>Test Listing</h1>
            <div class="price">€100,000</div>
            <div class="surface">50 m²</div>
        </div>
    </body>
    </html>
    '''
    mock_response.headers = {'content-type': 'text/html'}
    return mock_response


@pytest.fixture
def sample_html_content():
    """Fixture providing sample HTML content for parsing tests."""
    return '''
    <html>
    <head>
        <title>Test Property Listing</title>
    </head>
    <body>
        <div class="property-details">
            <h1 class="title">Beautiful Apartment in City Center</h1>
            <div class="price-container">
                <span class="price">€185,000</span>
                <span class="currency">EUR</span>
            </div>
            <div class="area-info">
                <span class="surface">85 m²</span>
            </div>
            <div class="location">
                <address>123 Main Street, 75001 Paris</address>
            </div>
            <div class="features">
                <span class="rooms">3 pièces</span>
                <span class="bedrooms">2 chambres</span>
                <span class="amenities">Balcon, Parking, Ascenseur</span>
            </div>
        </div>
    </body>
    </html>
    '''


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Auto-fixture that sets up test environment."""
    # Ensure test directories exist
    test_dirs = ["data", "logs", "config"]
    for dirname in test_dirs:
        Path(dirname).mkdir(exist_ok=True)
    
    yield
    
    # Cleanup could go here if needed


@pytest.fixture
def mock_etl_components():
    """Fixture providing mock ETL components."""
    mock_extractor = Mock()
    mock_transformer = Mock()  
    mock_validator = Mock()
    
    # Configure mock behaviors
    mock_extractor.extract.return_value = {"extracted": "data"}
    mock_transformer.transform.return_value = {"transformed": "data"}
    mock_validator.validate.return_value = True
    
    return {
        "extractor": mock_extractor,
        "transformer": mock_transformer,
        "validator": mock_validator
    }


# Custom test collection configuration
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to performance tests
        if "performance" in item.nodeid or "slow" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        
        # Add database marker to database tests
        if "database" in item.nodeid or "db" in item.nodeid:
            item.add_marker(pytest.mark.requires_database)


# Skip conditions
def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "slow: slow running tests")
    config.addinivalue_line("markers", "performance: performance tests")
    config.addinivalue_line("markers", "requires_docker: requires Docker")
    config.addinivalue_line("markers", "requires_database: requires database")
    config.addinivalue_line("markers", "requires_network: requires network access")
