"""
Tests for ETL deduplication module.
Tests duplicate detection and removal functionality.
"""

import pytest
import unittest
from unittest.mock import patch, MagicMock
from typing import Dict, List, Any

from etl.dedupe import (
    generate_listing_hash,
    dedupe_records,
    dedupe,
    find_duplicates,
    merge_duplicates
)


class TestHashGeneration:
    """Test hash generation for listing deduplication."""
    
    def test_generate_listing_hash_basic(self):
        """Test basic hash generation."""
        listing = {
            'url': 'https://example.com/listing1',
            'title': 'Beautiful Apartment',
            'address': '123 Main St',
            'price': 250000,
            'area_sqm': 85,
            'property_type': 'apartment'
        }
        
        hash_result = generate_listing_hash(listing)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 32  # MD5 hash length
    
    def test_generate_listing_hash_consistency(self):
        """Test that same listing produces same hash."""
        listing1 = {
            'url': 'https://example.com/listing1',
            'title': 'Beautiful Apartment',
            'price': 250000
        }
        listing2 = {
            'url': 'https://example.com/listing1',
            'title': 'Beautiful Apartment', 
            'price': 250000
        }
        
        hash1 = generate_listing_hash(listing1)
        hash2 = generate_listing_hash(listing2)
        assert hash1 == hash2
    
    def test_generate_listing_hash_different_listings(self):
        """Test that different listings produce different hashes."""
        listing1 = {'url': 'https://example.com/listing1', 'title': 'Apartment A'}
        listing2 = {'url': 'https://example.com/listing2', 'title': 'Apartment B'}
        
        hash1 = generate_listing_hash(listing1)
        hash2 = generate_listing_hash(listing2)
        assert hash1 != hash2
    
    def test_generate_listing_hash_missing_fields(self):
        """Test hash generation with missing fields."""
        listing = {'title': 'Apartment'}  # Missing other fields
        hash_result = generate_listing_hash(listing)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 32
    
    def test_generate_listing_hash_different(self):
        """Test that different listings produce different hashes."""
        listing1 = {
            'url': 'https://example.com/listing/123',
            'title': 'Beautiful Apartment',
            'price': 100000
        }
        
        listing2 = {
            'url': 'https://example.com/listing/456',  # Different URL
            'title': 'Beautiful Apartment',
            'price': 100000
        }
        
        hash1 = generate_listing_hash(listing1)
        hash2 = generate_listing_hash(listing2)
        
        assert hash1 != hash2
    
    def test_generate_listing_hash_missing_fields_partial(self):
        """Test hash generation with missing fields (partial data)."""
        listing1 = {'url': 'https://example.com/listing/123'}
        listing2 = {'title': 'Test', 'price': 50000}
        
        # Should not crash and produce valid hashes
        hash1 = generate_listing_hash(listing1)
        hash2 = generate_listing_hash(listing2)
        
        assert isinstance(hash1, str)
        assert isinstance(hash2, str)
        assert hash1 != hash2
    
    def test_generate_listing_hash_case_insensitive(self):
        """Test that hash generation is case insensitive."""
        listing1 = {
            'url': 'https://example.com/listing/123',
            'title': 'Beautiful Apartment'
        }
        
        listing2 = {
            'url': 'https://EXAMPLE.com/listing/123',
            'title': 'BEAUTIFUL APARTMENT'
        }
        
        hash1 = generate_listing_hash(listing1)
        hash2 = generate_listing_hash(listing2)
        
        assert hash1 == hash2


class TestDeduplication:
    """Test deduplication functionality."""
    
    def test_dedupe_records_empty_list(self):
        """Test deduplication with empty list."""
        result = dedupe_records([])
        assert result == []
    
    def test_dedupe_records_no_duplicates(self):
        """Test deduplication with no duplicates."""
        listings = [
            {'url': 'https://example.com/1', 'title': 'Listing 1'},
            {'url': 'https://example.com/2', 'title': 'Listing 2'},
            {'url': 'https://example.com/3', 'title': 'Listing 3'}
        ]
        
        result = dedupe_records(listings)
        assert len(result) == 3
        assert result == listings
    
    def test_dedupe_records_with_duplicates(self):
        """Test deduplication with actual duplicates."""
        listings = [
            {
                'url': 'https://example.com/1',
                'title': 'Apartment',
                'price': 100000,
                'address': '123 Main St'
            },
            {
                'url': 'https://example.com/2',
                'title': 'House',
                'price': 200000,
                'address': '456 Oak Ave'
            },
            {
                'url': 'https://example.com/1',  # Duplicate
                'title': 'Apartment',
                'price': 100000,
                'address': '123 Main St'
            }
        ]
        
        result = dedupe_records(listings)
        assert len(result) == 2  # Should remove one duplicate
        
        # Check that we kept the unique listings
        urls = [listing['url'] for listing in result]
        assert 'https://example.com/1' in urls
        assert 'https://example.com/2' in urls
    
    def test_dedupe_alias(self):
        """Test that dedupe alias works the same as dedupe_records."""
        listings = [
            {'url': 'https://example.com/1', 'title': 'Test 1'},
            {'url': 'https://example.com/1', 'title': 'Test 1'}  # Duplicate
        ]
        
        result1 = dedupe_records(listings)
        result2 = dedupe(listings)
        
        assert result1 == result2
    
    def test_dedupe_records_preserves_first_occurrence(self):
        """Test that deduplication preserves the first occurrence."""
        listings = [
            {
                'url': 'https://example.com/1',
                'title': 'Apartment',
                'extra_field': 'first'
            },
            {
                'url': 'https://example.com/1',
                'title': 'Apartment',
                'extra_field': 'second'  # This should be filtered out
            }
        ]
        
        result = dedupe_records(listings)
        assert len(result) == 1
        assert result[0]['extra_field'] == 'first'


class TestDuplicateDetection:
    """Test duplicate detection functionality."""
    
    def test_find_duplicates_none(self):
        """Test finding duplicates when there are none."""
        listings = [
            {'url': 'https://example.com/1', 'title': 'Listing 1'},
            {'url': 'https://example.com/2', 'title': 'Listing 2'}
        ]
        
        duplicates = find_duplicates(listings)
        assert len(duplicates) == 0
    
    def test_find_duplicates_present(self):
        """Test finding duplicates when they exist."""
        listings = [
            {'url': 'https://example.com/1', 'title': 'Listing 1'},
            {'url': 'https://example.com/2', 'title': 'Listing 2'},
            {'url': 'https://example.com/1', 'title': 'Listing 1'},  # Duplicate of index 0
            {'url': 'https://example.com/3', 'title': 'Listing 3'},
            {'url': 'https://example.com/2', 'title': 'Listing 2'}   # Duplicate of index 1
        ]
        
        duplicates = find_duplicates(listings)
        
        # Should find 2 groups of duplicates
        assert len(duplicates) == 2
        
        # Check that indices are correct
        for hash_value, indices in duplicates.items():
            assert len(indices) > 1  # Each group should have at least 2 items
    
    def test_find_duplicates_multiple_groups(self):
        """Test finding multiple groups of duplicates."""
        listings = [
            {'url': 'A', 'title': 'House'},      # Index 0
            {'url': 'B', 'title': 'Apartment'},  # Index 1
            {'url': 'A', 'title': 'House'},      # Index 2 - duplicate of 0
            {'url': 'C', 'title': 'Condo'},      # Index 3
            {'url': 'B', 'title': 'Apartment'},  # Index 4 - duplicate of 1
            {'url': 'A', 'title': 'House'}       # Index 5 - duplicate of 0
        ]
        
        duplicates = find_duplicates(listings)
        assert len(duplicates) == 2  # Two groups of duplicates
        
        # Check that we have correct groupings
        all_indices = []
        for indices in duplicates.values():
            all_indices.extend(indices)
        
        assert 0 in all_indices and 2 in all_indices and 5 in all_indices  # Group A
        assert 1 in all_indices and 4 in all_indices  # Group B


class TestDuplicateMerging:
    """Test duplicate merging functionality."""
    
    def test_merge_duplicates_no_duplicates(self):
        """Test merging when there are no duplicates."""
        listings = [
            {'url': 'A', 'title': 'House 1'},
            {'url': 'B', 'title': 'House 2'}
        ]
        
        result = merge_duplicates(listings)
        assert len(result) == 2
        assert result == listings
    
    def test_merge_duplicates_with_merging(self):
        """Test merging duplicates with complementary data."""
        listings = [
            {
                'url': 'https://example.com/1',
                'title': 'Apartment',
                'price': 100000,
                'address': '123 Main St'  # Same address
            },
            {
                'url': 'https://example.com/1',  # Same listing
                'title': 'Apartment',
                'price': 100000,
                'address': '123 Main St',  # Same address
                'rooms': 3  # Additional data
            }
        ]
        
        result = merge_duplicates(listings)
        assert len(result) == 1
        
        merged = result[0]
        assert merged['url'] == 'https://example.com/1'
        assert merged['title'] == 'Apartment'
        assert merged['price'] == 100000
        assert merged['address'] == '123 Main St'  # Address should be same
        assert merged['rooms'] == 3  # Should be added from duplicate
    
    def test_merge_duplicates_empty_list(self):
        """Test merging with empty list."""
        result = merge_duplicates([])
        assert result == []


class TestIntegrationScenarios:
    """Integration tests for deduplication scenarios."""
    
    def test_real_world_scenario(self):
        """Test a realistic deduplication scenario."""
        listings = [
            {
                'url': 'https://site1.com/apartment-123',
                'title': 'Beautiful 2BR Apartment',
                'price': 150000,
                'area_sqm': 75,
                'address': '123 Main Street, Paris',
                'property_type': 'apartment'
            },
            {
                'url': 'https://site2.com/listing-456',
                'title': 'Luxury House',
                'price': 500000,
                'area_sqm': 200,
                'address': '456 Oak Avenue, Lyon',
                'property_type': 'house'
            },
            {
                'url': 'https://site1.com/apartment-123',  # Exact duplicate
                'title': 'Beautiful 2BR Apartment',
                'price': 150000,
                'area_sqm': 75,
                'address': '123 Main Street, Paris',
                'property_type': 'apartment'
            },
            {
                'url': 'https://site3.com/property-789',
                'title': 'Studio Apartment',
                'price': 80000,
                'area_sqm': 30,
                'address': '789 Elm Street, Nice',
                'property_type': 'apartment'
            }
        ]
        
        # Test deduplication
        deduplicated = dedupe_records(listings)
        assert len(deduplicated) == 3  # Should remove 1 duplicate
        
        # Test duplicate detection
        duplicates = find_duplicates(listings)
        assert len(duplicates) == 1  # Should find 1 group of duplicates
        
        # Check that the duplicate group has 2 items
        for indices in duplicates.values():
            assert len(indices) == 2
            assert 0 in indices and 2 in indices  # First and third listings
    
    def test_case_sensitivity_deduplication(self):
        """Test that deduplication handles case differences correctly."""
        listings = [
            {
                'url': 'https://example.com/listing',
                'title': 'Beautiful Apartment',
                'address': '123 Main St'
            },
            {
                'url': 'https://EXAMPLE.com/listing',  # Different case in URL
                'title': 'BEAUTIFUL APARTMENT',  # Different case in title
                'address': '123 main st'  # Different case in address
            }
        ]
        
        # These should be considered duplicates due to case-insensitive hashing
        deduplicated = dedupe_records(listings)
        assert len(deduplicated) == 1
