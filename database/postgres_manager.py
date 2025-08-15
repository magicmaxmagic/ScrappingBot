#!/usr/bin/env python3
"""
PostgreSQL + PostGIS Manager for ScrappingBot
Handles connection, spatial operations, and data management
"""

import os
import json
import hashlib
import asyncio
import asyncpg
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from pathlib import Path
from dataclasses import dataclass
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ListingData:
    """Structured listing data for database insertion"""
    url: str
    title: Optional[str] = None
    price: Optional[float] = None
    currency: str = 'CAD'
    area_sqm: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    property_type: Optional[str] = None
    listing_type: str = 'sale'
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    site_domain: Optional[str] = None
    published_date: Optional[date] = None
    monthly_rent: Optional[float] = None
    raw_data: Optional[Dict] = None

class PostgreSQLManager:
    """Manages PostgreSQL connection and operations for ScrappingBot"""
    
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or self._get_connection_string()
        self.pool: Optional[asyncpg.Pool] = None
        
    def _get_connection_string(self) -> str:
        """Get PostgreSQL connection string from environment or config"""
        # Try environment variables first
        if 'DATABASE_URL' in os.environ:
            return os.environ['DATABASE_URL']
        
        # Default local PostgreSQL
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        user = os.getenv('POSTGRES_USER', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        database = os.getenv('POSTGRES_DB', 'scrappingbot')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    async def init_pool(self):
        """Initialize connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise
    
    async def close_pool(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool"""
        if self.pool is None:
            await self.init_pool()
        if self.pool is None:
            raise RuntimeError("PostgreSQL connection pool is not initialized.")
        
        async with self.pool.acquire() as connection:
            yield connection
    
    @staticmethod
    def generate_url_hash(url: str) -> str:
        """Generate SHA-256 hash of URL for duplicate detection"""
        return hashlib.sha256(url.encode()).hexdigest()
    
    async def load_montreal_areas(self, geojson_file: str) -> int:
        """Load Montreal neighborhoods from GeoJSON file"""
        geojson_path = Path(geojson_file)
        if not geojson_path.exists():
            logger.error(f"GeoJSON file not found: {geojson_file}")
            return 0
        
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        inserted_count = 0
        
        async with self.get_connection() as conn:
            for feature in geojson_data.get('features', []):
                properties = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                
                name = properties.get('NOM', properties.get('name', 'Unknown'))
                
                # Convert GeoJSON geometry to PostGIS format
                geometry_json = json.dumps(geometry)
                
                try:
                    await conn.execute("""
                        INSERT INTO areas (name, city, province, geometry)
                        VALUES ($1, $2, $3, ST_GeomFromGeoJSON($4))
                        ON CONFLICT (name, city) DO UPDATE SET
                            geometry = ST_GeomFromGeoJSON($4),
                            updated_at = NOW()
                    """, name, 'Montreal', 'QC', geometry_json)
                    
                    inserted_count += 1
                    logger.info(f"Loaded area: {name}")
                    
                except Exception as e:
                    logger.error(f"Failed to insert area {name}: {e}")
        
        logger.info(f"Loaded {inserted_count} Montreal areas")
        return inserted_count
    
    async def upsert_listing(self, listing: ListingData) -> str:
        """Insert or update a listing, returns UUID"""
        url_hash = self.generate_url_hash(listing.url)
        
        async with self.get_connection() as conn:
            # Prepare coordinates
            coordinates = None
            if listing.latitude and listing.longitude:
                coordinates = f"POINT({listing.longitude} {listing.latitude})"
            
            # Insert or update
            result = await conn.fetchrow("""
                INSERT INTO listings (
                    url_hash, url, title, price, currency, area_sqm,
                    bedrooms, bathrooms, property_type, listing_type,
                    address, coordinates, site_domain, published_date,
                    monthly_rent, raw_data
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, ST_GeomFromText($12, 4326), $13, $14, $15, $16
                )
                ON CONFLICT (url_hash) DO UPDATE SET
                    title = EXCLUDED.title,
                    price = EXCLUDED.price,
                    area_sqm = EXCLUDED.area_sqm,
                    bedrooms = EXCLUDED.bedrooms,
                    bathrooms = EXCLUDED.bathrooms,
                    property_type = EXCLUDED.property_type,
                    listing_type = EXCLUDED.listing_type,
                    address = EXCLUDED.address,
                    coordinates = EXCLUDED.coordinates,
                    site_domain = EXCLUDED.site_domain,
                    published_date = EXCLUDED.published_date,
                    monthly_rent = EXCLUDED.monthly_rent,
                    raw_data = EXCLUDED.raw_data,
                    updated_at = NOW()
                RETURNING id
            """, 
                url_hash, listing.url, listing.title, listing.price,
                listing.currency, listing.area_sqm, listing.bedrooms,
                listing.bathrooms, listing.property_type, listing.listing_type,
                listing.address, coordinates, listing.site_domain,
                listing.published_date, listing.monthly_rent,
                json.dumps(listing.raw_data) if listing.raw_data else None
            )
            
            listing_id = result['id']
            logger.info(f"Upserted listing {listing_id} for {listing.url}")
            return str(listing_id)
    
    async def log_scrape_attempt(self, source: str, url: str, status: str,
                                listings_found: int = 0, response_time_ms: int = 0,
                                strategy_used: str = 'dom', error_message: Optional[str] = None):
        """Log a scraping attempt"""
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT INTO scrape_logs (
                    source, url, status, listings_found, response_time_ms,
                    strategy_used, error_message
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, source, url, status, listings_found, response_time_ms,
                 strategy_used, error_message)
    
    async def get_listings_by_area(self, area_name: Optional[str] = None,
                                   limit: int = 100) -> List[Dict]:
        """Get listings with area information"""
        async with self.get_connection() as conn:
            if area_name:
                query = """
                    SELECT l.*, a.name as area_name, a.city, a.province,
                           ST_X(l.coordinates) as longitude,
                           ST_Y(l.coordinates) as latitude
                    FROM listings l
                    LEFT JOIN areas a ON l.area_id = a.id
                    WHERE a.name ILIKE $1 AND l.is_active = true
                    ORDER BY l.scraped_at DESC
                    LIMIT $2
                """
                rows = await conn.fetch(query, f"%{area_name}%", limit)
            else:
                query = """
                    SELECT l.*, a.name as area_name, a.city, a.province,
                           ST_X(l.coordinates) as longitude,
                           ST_Y(l.coordinates) as latitude
                    FROM listings l
                    LEFT JOIN areas a ON l.area_id = a.id
                    WHERE l.is_active = true
                    ORDER BY l.scraped_at DESC
                    LIMIT $1
                """
                rows = await conn.fetch(query, limit)
            
            return [dict(row) for row in rows]
    
    async def get_listings_in_polygon(self, polygon_coords: List[Tuple[float, float]],
                                     limit: int = 100) -> List[Dict]:
        """Get listings within a polygon (for map filtering)"""
        # Convert coordinates to WKT polygon format
        coords_str = ", ".join([f"{lon} {lat}" for lat, lon in polygon_coords])
        # Close the polygon
        if polygon_coords[0] != polygon_coords[-1]:
            coords_str += f", {polygon_coords[0][1]} {polygon_coords[0][0]}"
        
        polygon_wkt = f"POLYGON(({coords_str}))"
        
        async with self.get_connection() as conn:
            query = """
                SELECT l.*, a.name as area_name, a.city, a.province,
                       ST_X(l.coordinates) as longitude,
                       ST_Y(l.coordinates) as latitude
                FROM listings l
                LEFT JOIN areas a ON l.area_id = a.id
                WHERE l.coordinates IS NOT NULL
                  AND ST_Within(l.coordinates, ST_GeomFromText($1, 4326))
                  AND l.is_active = true
                ORDER BY l.scraped_at DESC
                LIMIT $2
            """
            rows = await conn.fetch(query, polygon_wkt, limit)
            return [dict(row) for row in rows]
    
    async def get_area_metrics(self, days_back: int = 30) -> List[Dict]:
        """Get area metrics for dashboard"""
        async with self.get_connection() as conn:
            query = """
                SELECT am.*, a.name as area_name, a.city
                FROM area_metrics am
                JOIN areas a ON am.area_id = a.id
                WHERE am.metric_date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY am.metric_date DESC, a.name
            """
            rows = await conn.fetch(query % days_back)
            return [dict(row) for row in rows]
    
    async def refresh_materialized_views(self):
        """Refresh materialized views for better performance"""
        async with self.get_connection() as conn:
            await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY listings_summary")
            logger.info("Refreshed materialized views")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        async with self.get_connection() as conn:
            stats = {}
            
            # Total listings
            result = await conn.fetchrow("SELECT COUNT(*) as count FROM listings WHERE is_active = true")
            stats['total_listings'] = result['count']
            
            # Listings by area
            result = await conn.fetch("""
                SELECT a.name, COUNT(l.id) as count
                FROM areas a
                LEFT JOIN listings l ON l.area_id = a.id AND l.is_active = true
                GROUP BY a.id, a.name
                ORDER BY count DESC
                LIMIT 10
            """)
            stats['top_areas'] = [dict(row) for row in result]
            
            # Price statistics
            result = await conn.fetchrow("""
                SELECT 
                    AVG(price) as avg_price,
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    COUNT(*) FILTER (WHERE price > 0) as priced_listings
                FROM listings 
                WHERE is_active = true AND price > 0
            """)
            stats['price_stats'] = dict(result)
            
            # Recent activity
            result = await conn.fetchrow("""
                SELECT COUNT(*) as count
                FROM listings
                WHERE scraped_at >= NOW() - INTERVAL '24 hours'
            """)
            stats['listings_24h'] = result['count']
            
            return stats

async def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PostgreSQL Manager for ScrappingBot")
    parser.add_argument('--init-schema', help='Initialize database schema from file')
    parser.add_argument('--load-areas', help='Load Montreal areas from GeoJSON file')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--refresh-views', action='store_true', help='Refresh materialized views')
    args = parser.parse_args()
    
    db = PostgreSQLManager()
    
    try:
        await db.init_pool()
        
        if args.init_schema:
            # Execute schema file
            schema_path = Path(args.init_schema)
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                
                async with db.get_connection() as conn:
                    await conn.execute(schema_sql)
                logger.info(f"Executed schema from {args.init_schema}")
            else:
                logger.error(f"Schema file not found: {args.init_schema}")
        
        if args.load_areas:
            count = await db.load_montreal_areas(args.load_areas)
            logger.info(f"Loaded {count} areas from {args.load_areas}")
        
        if args.stats:
            stats = await db.get_stats()
            print(json.dumps(stats, indent=2, default=str))
        
        if args.refresh_views:
            await db.refresh_materialized_views()
    
    finally:
        await db.close_pool()

if __name__ == "__main__":
    asyncio.run(main())
