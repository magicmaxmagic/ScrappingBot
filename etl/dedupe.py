"""
Data deduplication utilities for the ETL pipeline.
Removes duplicate listings based on various criteria.
"""

import hashlib
from typing import List, Dict, Any, Set


def generate_listing_hash(listing: Dict[str, Any]) -> str:
    """
    Generate a hash for a listing based on key identifying fields.
    
    Args:
        listing: Listing dictionary
        
    Returns:
        Hash string for deduplication
    """
    # Key fields for identifying duplicates
    key_fields = [
        'url',
        'title', 
        'address',
        'price',
        'area_sqm',
        'property_type'
    ]
    
    # Create hash input string
    hash_input = ""
    for field in key_fields:
        value = listing.get(field, "")
        if value is not None:
            hash_input += str(value).lower().strip()
    
    # Generate MD5 hash
    return hashlib.md5(hash_input.encode('utf-8')).hexdigest()


def dedupe_records(listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate listings from a list.
    
    Args:
        listings: List of listing dictionaries
        
    Returns:
        Deduplicated list of listings
    """
    if not listings:
        return []
    
    seen_hashes: Set[str] = set()
    deduplicated = []
    
    for listing in listings:
        listing_hash = generate_listing_hash(listing)
        
        if listing_hash not in seen_hashes:
            seen_hashes.add(listing_hash)
            deduplicated.append(listing)
    
    return deduplicated


def dedupe(listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Alias for dedupe_records for backward compatibility."""
    return dedupe_records(listings)


def find_duplicates(listings: List[Dict[str, Any]]) -> Dict[str, List[int]]:
    """
    Find duplicate listings and return their indices.
    
    Args:
        listings: List of listing dictionaries
        
    Returns:
        Dictionary mapping hash to list of indices
    """
    hash_to_indices: Dict[str, List[int]] = {}
    
    for i, listing in enumerate(listings):
        listing_hash = generate_listing_hash(listing)
        
        if listing_hash not in hash_to_indices:
            hash_to_indices[listing_hash] = []
        
        hash_to_indices[listing_hash].append(i)
    
    # Return only duplicates (hash with more than one index)
    return {h: indices for h, indices in hash_to_indices.items() if len(indices) > 1}


def merge_duplicates(listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge duplicate listings by combining their data.
    
    Args:
        listings: List of listing dictionaries
        
    Returns:
        List with merged duplicates
    """
    if not listings:
        return []
    
    duplicates = find_duplicates(listings)
    used_indices: Set[int] = set()
    merged_listings = []
    
    # Process duplicates
    for hash_value, indices in duplicates.items():
        if not any(i in used_indices for i in indices):
            # Merge all duplicates for this hash
            merged = listings[indices[0]].copy()
            
            # Merge data from other duplicates
            for i in indices[1:]:
                duplicate = listings[i]
                for key, value in duplicate.items():
                    if not merged.get(key) and value:
                        merged[key] = value
            
            merged_listings.append(merged)
            used_indices.update(indices)
    
    # Add non-duplicates
    for i, listing in enumerate(listings):
        if i not in used_indices:
            merged_listings.append(listing)
    
    return merged_listings
