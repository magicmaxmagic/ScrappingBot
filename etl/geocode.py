"""
Geocoding utilities for the ETL pipeline.
Handles address geocoding and neighborhood detection.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import requests


logger = logging.getLogger(__name__)


def geocode_address(address: str, timeout: int = 5) -> Optional[Tuple[float, float]]:
    """
    Geocode an address using a free geocoding service.
    
    Args:
        address: Address string to geocode
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    if not address:
        return None
    
    try:
        # Use Nominatim (OpenStreetMap) geocoding service
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'fr',  # Focus on France
        }
        
        headers = {
            'User-Agent': 'ScrappingBot/1.0 (https://github.com/magicmaxmagic/ScrappingBot)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        data = response.json()
        if data and len(data) > 0:
            result = data[0]
            lat = float(result['lat'])
            lon = float(result['lon'])
            return (lat, lon)
    
    except Exception as e:
        logger.warning(f"Geocoding failed for address '{address}': {e}")
    
    return None


def geocode(address: str, timeout: int = 5) -> Optional[Tuple[float, float]]:
    """Alias for geocode_address for backward compatibility."""
    return geocode_address(address, timeout)


def neighborhood_from_geojson(
    latitude: float, 
    longitude: float, 
    geojson_path: str
) -> Optional[str]:
    """
    Find neighborhood from coordinates using a GeoJSON file.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        geojson_path: Path to GeoJSON file with neighborhood boundaries
        
    Returns:
        Neighborhood name or None if not found
    """
    try:
        geojson_file = Path(geojson_path)
        if not geojson_file.exists():
            logger.warning(f"GeoJSON file not found: {geojson_path}")
            return None
        
        with open(geojson_file, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        # Simple point-in-polygon check for each feature
        for feature in geojson_data.get('features', []):
            if point_in_polygon(latitude, longitude, feature):
                # Try different property names for neighborhood
                properties = feature.get('properties', {})
                for name_field in ['nom', 'name', 'neighborhood', 'quartier', 'district']:
                    if name_field in properties:
                        return properties[name_field]
    
    except Exception as e:
        logger.warning(f"Error finding neighborhood: {e}")
    
    return None


def point_in_polygon(lat: float, lon: float, feature: Dict[str, Any]) -> bool:
    """
    Check if a point is inside a polygon feature using ray casting algorithm.
    
    Args:
        lat: Point latitude
        lon: Point longitude
        feature: GeoJSON feature
        
    Returns:
        True if point is inside polygon
    """
    try:
        geometry = feature.get('geometry', {})
        if geometry.get('type') != 'Polygon':
            return False
        
        coordinates = geometry.get('coordinates', [])
        if not coordinates:
            return False
        
        # Use first polygon ring (exterior)
        polygon = coordinates[0]
        
        # Ray casting algorithm
        inside = False
        j = len(polygon) - 1
        
        for i in range(len(polygon)):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            
            if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
                inside = not inside
            
            j = i
        
        return inside
    
    except Exception as e:
        logger.warning(f"Error in point-in-polygon calculation: {e}")
        return False


def reverse_geocode(latitude: float, longitude: float, timeout: int = 5) -> Optional[str]:
    """
    Reverse geocode coordinates to get address.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate  
        timeout: Request timeout in seconds
        
    Returns:
        Address string or None if reverse geocoding fails
    """
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
            'zoom': 16,
            'countrycodes': 'fr',
        }
        
        headers = {
            'User-Agent': 'ScrappingBot/1.0 (https://github.com/magicmaxmagic/ScrappingBot)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        data = response.json()
        return data.get('display_name')
    
    except Exception as e:
        logger.warning(f"Reverse geocoding failed for {latitude}, {longitude}: {e}")
    
    return None
