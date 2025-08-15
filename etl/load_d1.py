"""
Database loading utilities for the ETL pipeline.
Generates SQL for upserting listings into PostgreSQL.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime


def generate_upsert_sql(listings: List[Dict[str, Any]]) -> str:
    """
    Generate SQL for upserting listings into the database.
    
    Args:
        listings: List of listing dictionaries
        
    Returns:
        SQL string with UPSERT statements
    """
    if not listings:
        return "-- No listings to insert\n"
    
    sql_parts = [
        "-- Generated UPSERT SQL for listings",
        f"-- Generated at: {datetime.now().isoformat()}",
        f"-- Total listings: {len(listings)}",
        "",
        "BEGIN;",
        ""
    ]
    
    for i, listing in enumerate(listings):
        sql_parts.append(f"-- Listing {i+1}: {listing.get('url', 'unknown')}")
        sql_parts.append(_generate_single_upsert(listing))
        sql_parts.append("")
    
    sql_parts.extend([
        "COMMIT;",
        "",
        f"-- Successfully processed {len(listings)} listings"
    ])
    
    return "\n".join(sql_parts)


def _generate_single_upsert(listing: Dict[str, Any]) -> str:
    """
    Generate UPSERT SQL for a single listing.
    
    Args:
        listing: Single listing dictionary
        
    Returns:
        SQL UPSERT statement
    """
    # Define column mappings (database column -> listing key)
    column_mappings = {
        'url': 'url',
        'title': 'title', 
        'description': 'description',
        'property_type': 'property_type',
        'price': 'price',
        'currency': 'currency',
        'area': 'area',
        'area_unit': 'area_unit',
        'area_sqm': 'area_sqm',
        'address': 'address',
        'city': 'city',
        'postal_code': 'postal_code',
        'neighborhood': 'neighborhood',
        'latitude': 'latitude',
        'longitude': 'longitude',
        'rooms': 'rooms',
        'bedrooms': 'bedrooms',
        'bathrooms': 'bathrooms',
        'floor': 'floor',
        'balcony': 'balcony',
        'parking': 'parking',
        'garden': 'garden',
        'elevator': 'elevator',
        'source': 'source',
        'scraped_at': 'scraped_at',
        'updated_at': 'updated_at'
    }
    
    # Prepare values
    columns = []
    values = []
    updates = []
    
    for db_col, listing_key in column_mappings.items():
        if listing_key in listing and listing[listing_key] is not None:
            columns.append(db_col)
            value = _format_sql_value(listing[listing_key])
            values.append(value)
            
            # Add to UPDATE clause (except for URL which is the key)
            if db_col != 'url':
                updates.append(f"{db_col} = EXCLUDED.{db_col}")
    
    # Add coordinates as PostGIS geometry if both lat/lon exist
    if 'latitude' in listing and 'longitude' in listing:
        lat = listing['latitude']
        lon = listing['longitude']
        if lat is not None and lon is not None:
            columns.append('location')
            values.append(f"ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)")
            updates.append("location = EXCLUDED.location")
    
    # Always update the updated_at timestamp
    columns.append('updated_at')
    values.append('NOW()')
    updates.append('updated_at = EXCLUDED.updated_at')
    
    # Build SQL
    sql = f"""INSERT INTO listings ({', '.join(columns)})
VALUES ({', '.join(values)})
ON CONFLICT (url) DO UPDATE SET
    {', '.join(updates)};"""
    
    return sql


def _format_sql_value(value: Any) -> str:
    """
    Format a Python value for SQL insertion.
    
    Args:
        value: Python value
        
    Returns:
        SQL-formatted string
    """
    if value is None:
        return "NULL"
    
    elif isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    
    elif isinstance(value, (int, float)):
        return str(value)
    
    elif isinstance(value, str):
        # Escape single quotes and wrap in quotes
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    
    elif isinstance(value, datetime):
        return f"'{value.isoformat()}'"
    
    elif isinstance(value, (list, dict)):
        # Convert to JSON
        json_str = json.dumps(value).replace("'", "''")
        return f"'{json_str}'"
    
    else:
        # Convert to string and escape
        str_value = str(value).replace("'", "''")
        return f"'{str_value}'"


def generate_delete_sql(urls: List[str]) -> str:
    """
    Generate SQL for deleting listings by URL.
    
    Args:
        urls: List of URLs to delete
        
    Returns:
        SQL DELETE statement
    """
    if not urls:
        return "-- No listings to delete\n"
    
    url_list = "', '".join(url.replace("'", "''") for url in urls)
    
    sql = f"""-- Delete listings by URL
-- Generated at: {datetime.now().isoformat()}
-- URLs to delete: {len(urls)}

BEGIN;

DELETE FROM listings 
WHERE url IN ('{url_list}');

COMMIT;

-- Deleted listings for {len(urls)} URLs
"""
    
    return sql


def generate_cleanup_sql(days_old: int = 30) -> str:
    """
    Generate SQL for cleaning up old listings.
    
    Args:
        days_old: Delete listings older than this many days
        
    Returns:
        SQL DELETE statement
    """
    sql = f"""-- Cleanup old listings
-- Generated at: {datetime.now().isoformat()}
-- Remove listings older than {days_old} days

BEGIN;

-- Delete listings not updated in the last {days_old} days
DELETE FROM listings 
WHERE updated_at < NOW() - INTERVAL '{days_old} days';

-- Get count of remaining listings
SELECT COUNT(*) as remaining_listings FROM listings;

COMMIT;
"""
    
    return sql
