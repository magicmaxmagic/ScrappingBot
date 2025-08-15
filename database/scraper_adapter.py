#!/usr/bin/env python3
"""
PostgreSQL Integration Adapter for RealEstateScraper
Extends existing scraper to save data to PostgreSQL+PostGIS
"""

import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))

from database.postgres_manager import PostgreSQLManager, ListingData
from scraper.spiders.clean_scraper import RealEstateScraper

logger = logging.getLogger(__name__)

class PostgreSQLScraperAdapter:
    """Adapter to save scraping results to PostgreSQL"""
    
    def __init__(self, db_manager: PostgreSQLManager):
        self.db_manager = db_manager
        
    def extract_site_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return None
    
    def parse_price(self, price_raw: Any) -> Optional[float]:
        """Parse price from various formats"""
        if not price_raw:
            return None
            
        try:
            if isinstance(price_raw, (int, float)):
                return float(price_raw)
            
            # Remove currency symbols and spaces
            price_str = str(price_raw).replace('$', '').replace(',', '').replace(' ', '')
            return float(price_str) if price_str.replace('.', '').isdigit() else None
        except:
            return None
    
    def parse_date(self, date_str: Any) -> Optional[date]:
        """Parse date from various formats"""
        if not date_str:
            return None
            
        try:
            if isinstance(date_str, date):
                return date_str
            
            # Try common date formats
            date_formats = [
                '%Y-%m-%d',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%m/%d/%Y',
                '%d/%m/%Y'
            ]
            
            for fmt in date_formats:
                try:
                    parsed = datetime.strptime(str(date_str), fmt)
                    return parsed.date()
                except:
                    continue
        except:
            pass
            
        return None
    
    def convert_to_listing_data(self, raw_listing: Dict, source: str = "realtor") -> Optional[ListingData]:
        """Convert scraped data to ListingData format"""
        try:
            # Required URL
            url = raw_listing.get('url')
            if not url:
                return None
            
            # Parse coordinates
            latitude = None
            longitude = None
            
            # Try different coordinate formats
            if 'lat' in raw_listing and 'lng' in raw_listing:
                latitude = float(raw_listing['lat'])
                longitude = float(raw_listing['lng'])
            elif 'latitude' in raw_listing and 'longitude' in raw_listing:
                latitude = float(raw_listing['latitude'])
                longitude = float(raw_listing['longitude'])
            elif 'coordinates' in raw_listing:
                coords = raw_listing['coordinates']
                if isinstance(coords, dict):
                    latitude = coords.get('lat') or coords.get('latitude')
                    longitude = coords.get('lng') or coords.get('longitude')
                elif isinstance(coords, list) and len(coords) == 2:
                    longitude, latitude = coords  # GeoJSON format [lng, lat]
            
            # Convert to float if needed
            if latitude:
                latitude = float(latitude)
            if longitude:
                longitude = float(longitude)
            
            return ListingData(
                url=url,
                title=raw_listing.get('title') or raw_listing.get('name'),
                price=self.parse_price(raw_listing.get('price') or raw_listing.get('price_raw')),
                currency=raw_listing.get('currency', 'CAD'),
                area_sqm=float(raw_listing['area_sqm']) if raw_listing.get('area_sqm') else None,
                bedrooms=int(raw_listing['bedrooms']) if raw_listing.get('bedrooms') else None,
                bathrooms=float(raw_listing['bathrooms']) if raw_listing.get('bathrooms') else None,
                property_type=raw_listing.get('property_type') or raw_listing.get('type'),
                listing_type=raw_listing.get('listing_type', 'sale'),
                address=raw_listing.get('address'),
                latitude=latitude,
                longitude=longitude,
                site_domain=self.extract_site_domain(url) or source,
                published_date=self.parse_date(raw_listing.get('published_date') or raw_listing.get('date')),
                monthly_rent=self.parse_price(raw_listing.get('monthly_rent')) if raw_listing.get('listing_type') == 'rent' else None,
                raw_data=raw_listing  # Store original data for analysis
            )
            
        except Exception as e:
            logger.error(f"Failed to convert listing data: {e}")
            logger.debug(f"Raw listing: {raw_listing}")
            return None
    
    async def save_listings(self, listings: List[Dict], source: str, scrape_url: str) -> int:
        """Save scraped listings to PostgreSQL"""
        if not listings:
            return 0
        
        saved_count = 0
        
        for raw_listing in listings:
            try:
                listing_data = self.convert_to_listing_data(raw_listing, source)
                if listing_data:
                    await self.db_manager.upsert_listing(listing_data)
                    saved_count += 1
            except Exception as e:
                logger.error(f"Failed to save listing: {e}")
                continue
        
        # Log the scrape attempt
        status = "success" if saved_count > 0 else "empty"
        await self.db_manager.log_scrape_attempt(
            source=source,
            url=scrape_url,
            status=status,
            listings_found=saved_count,
            strategy_used="mixed"
        )
        
        logger.info(f"Saved {saved_count}/{len(listings)} listings to PostgreSQL")
        return saved_count

class EnhancedRealEstateScraper(RealEstateScraper):
    """Extended scraper with PostgreSQL integration"""
    
    def __init__(self, headless: bool = True, timeout_ms: int = 30000, 
                 debug: bool = False, use_postgres: bool = True):
        super().__init__(headless, timeout_ms, debug)
        self.use_postgres = use_postgres
        self.db_manager = None
        self.pg_adapter = None
    
    async def __aenter__(self):
        await super().__aenter__()
        
        if self.use_postgres:
            try:
                self.db_manager = PostgreSQLManager()
                await self.db_manager.init_pool()
                self.pg_adapter = PostgreSQLScraperAdapter(self.db_manager)
                logger.info("PostgreSQL integration enabled")
            except Exception as e:
                logger.warning(f"PostgreSQL integration failed, falling back to JSON: {e}")
                self.use_postgres = False
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.db_manager:
            await self.db_manager.close_pool()
        await super().__aexit__(exc_type, exc_val, exc_tb)
    
    async def write_preview(self, listings: List[Dict], source: str, blocked: bool, 
                           strategy: str, error: Optional[str] = None):
        """Enhanced preview that also saves to PostgreSQL"""
        # Always write JSON preview for immediate feedback
        preview_path = await super().write_preview(listings, source, blocked, strategy, error)
        
        # Also save to PostgreSQL if enabled and we have listings
        if self.use_postgres and self.pg_adapter and listings and not blocked:
            try:
                search_url = f"https://{source}.com/search"  # Approximation
                saved_count = await self.pg_adapter.save_listings(listings, source, search_url)
                logger.info(f"PostgreSQL: Saved {saved_count} listings")
            except Exception as e:
                logger.error(f"PostgreSQL save failed: {e}")
        
        return preview_path

async def main():
    """Enhanced CLI with PostgreSQL support"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced scraper with PostgreSQL")
    parser.add_argument('--where', required=True, help='City/location to search')
    parser.add_argument('--what', required=True, help='Property type (condo, house, etc)')
    parser.add_argument('--when', default='all', help='Date filter')
    parser.add_argument('--start_url', help='Direct URL to scrape')
    parser.add_argument('--source', default='realtor', help='Source name')
    parser.add_argument('--dom', action='store_true', help='Force DOM extraction')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    parser.add_argument('--headless', action='store_true', default=True, help='Headless browser')
    parser.add_argument('--timeout', type=int, default=30000, help='Timeout (ms)')
    parser.add_argument('--no-postgres', action='store_true', help='Disable PostgreSQL integration')
    
    args = parser.parse_args()
    
    logger.info(f"Enhanced scraper: {args.source} - {args.where} {args.what}")
    
    try:
        async with EnhancedRealEstateScraper(
            headless=args.headless,
            timeout_ms=args.timeout,
            debug=args.debug,
            use_postgres=not args.no_postgres
        ) as scraper:
            
            result = await scraper.scrape(
                where=args.where,
                what=args.what,
                when=args.when,
                start_url=args.start_url,
                force_dom=args.dom,
                source=args.source
            )
            
            if result.get("blocked"):
                logger.warning(f"Blocked: {result.get('reason')}")
                return 2
            elif result.get("success"):
                logger.info(f"Success: {result.get('count')} listings")
                return 0
            else:
                logger.error(f"Failed: {result.get('error')}")
                return 1
                
    except Exception as e:
        logger.error(f"Critical error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
