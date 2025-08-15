#!/usr/bin/env python3
"""
FastAPI service for ScrappingBot PostgreSQL data
Provides REST API endpoints for real estate listings
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import sys

# Add database module to path
sys.path.append('/app')
from database.postgres_manager import PostgreSQLManager, ListingData

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://scrappingbot_user:scrappingbot_pass@postgres:5432/scrappingbot')
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')

app = FastAPI(
    title="ScrappingBot API",
    description="REST API for real estate data with spatial operations",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global database manager
db_manager: Optional[PostgreSQLManager] = None

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    global db_manager
    try:
        db_manager = PostgreSQLManager(DATABASE_URL)
        await db_manager.init_pool()
        logger.info("Database connection initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    global db_manager
    if db_manager:
        await db_manager.close_pool()
        logger.info("Database connection closed")

async def get_db() -> PostgreSQLManager:
    """Dependency to get database manager"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    return db_manager

# Pydantic models
class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None

class ListingFilter(BaseModel):
    area: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    property_type: Optional[str] = None
    listing_type: Optional[str] = None
    limit: int = 50
    offset: int = 0
    bbox: Optional[str] = None  # "west,south,east,north"

@app.get("/")
async def root():
    return {"message": "ScrappingBot API", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check(db: PostgreSQLManager = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        stats = await db.get_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": "connected",
                "api": "running"
            },
            "stats": {
                "total_listings": stats.get('total_listings', 0)
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/api/listings", response_model=ApiResponse)
async def get_listings(
    area: Optional[str] = Query(None, description="Filter by area name"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    property_type: Optional[str] = Query(None, description="Property type filter"),
    listing_type: Optional[str] = Query(None, description="Listing type (sale/rent)"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    bbox: Optional[str] = Query(None, description="Bounding box: west,south,east,north"),
    db: PostgreSQLManager = Depends(get_db)
):
    """Get listings with optional filters"""
    try:
        # Handle bounding box query
        if bbox:
            try:
                coords = [float(x) for x in bbox.split(',')]
                if len(coords) == 4:
                    west, south, east, north = coords
                    polygon_coords = [
                        (west, south), (east, south), 
                        (east, north), (west, north), (west, south)
                    ]
                    results = await db.get_listings_in_polygon(polygon_coords, limit)
                else:
                    raise ValueError("Invalid bbox format")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid bbox format. Use: west,south,east,north")
        else:
            # Regular area-based query
            results = await db.get_listings_by_area(area, limit)
        
        # Apply additional filters
        filtered_results = []
        for listing in results:
            # Skip if outside price range
            if min_price is not None and (listing.get('price') or 0) < min_price:
                continue
            if max_price is not None and (listing.get('price') or float('inf')) > max_price:
                continue
            
            # Skip if property type doesn't match
            if property_type and listing.get('property_type'):
                if property_type.lower() not in listing['property_type'].lower():
                    continue
            
            # Skip if listing type doesn't match
            if listing_type and listing.get('listing_type') != listing_type:
                continue
            
            filtered_results.append(listing)
        
        # Apply pagination
        paginated_results = filtered_results[offset:offset + limit]
        
        return ApiResponse(
            success=True,
            data=paginated_results,
            metadata={
                "total": len(filtered_results),
                "limit": limit,
                "offset": offset,
                "returned": len(paginated_results)
            }
        )
        
    except Exception as e:
        logger.error(f"Get listings error: {e}")
        return ApiResponse(success=False, error=str(e))

@app.get("/api/areas/stats", response_model=ApiResponse)
async def get_area_stats(db: PostgreSQLManager = Depends(get_db)):
    """Get area statistics"""
    try:
        stats = await db.get_area_metrics()
        return ApiResponse(success=True, data=stats)
    except Exception as e:
        logger.error(f"Get area stats error: {e}")
        return ApiResponse(success=False, error=str(e))

@app.get("/api/activity", response_model=ApiResponse)  
async def get_recent_activity(
    days: int = Query(7, ge=1, le=30, description="Days back to fetch activity"),
    db: PostgreSQLManager = Depends(get_db)
):
    """Get recent scraping activity"""
    try:
        stats = await db.get_area_metrics(days_back=days)
        return ApiResponse(success=True, data=stats)
    except Exception as e:
        logger.error(f"Get activity error: {e}")
        return ApiResponse(success=False, error=str(e))

@app.get("/api/stats", response_model=ApiResponse)
async def get_database_stats(db: PostgreSQLManager = Depends(get_db)):
    """Get overall database statistics"""
    try:
        stats = await db.get_stats()
        return ApiResponse(success=True, data=stats)
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        return ApiResponse(success=False, error=str(e))

@app.post("/api/listings", response_model=ApiResponse)
async def create_listing(
    listing: dict,
    db: PostgreSQLManager = Depends(get_db)
):
    """Create a new listing (for testing)"""
    try:
        # Convert dict to ListingData
        listing_data = ListingData(
            url=listing.get('url', ''),
            title=listing.get('title'),
            price=listing.get('price'),
            currency=listing.get('currency', 'CAD'),
            area_sqm=listing.get('area_sqm'),
            bedrooms=listing.get('bedrooms'),
            bathrooms=listing.get('bathrooms'),
            property_type=listing.get('property_type'),
            listing_type=listing.get('listing_type', 'sale'),
            address=listing.get('address'),
            latitude=listing.get('latitude'),
            longitude=listing.get('longitude'),
            site_domain=listing.get('site_domain', 'api'),
            published_date=listing.get('published_date'),
            raw_data=listing
        )
        
        listing_id = await db.upsert_listing(listing_data)
        
        return ApiResponse(
            success=True,
            data={"id": listing_id, "message": "Listing created successfully"}
        )
        
    except Exception as e:
        logger.error(f"Create listing error: {e}")
        return ApiResponse(success=False, error=str(e))

@app.get("/api/areas", response_model=ApiResponse)
async def get_areas(db: PostgreSQLManager = Depends(get_db)):
    """Get all available areas"""
    try:
        async with db.get_connection() as conn:
            results = await conn.fetch("""
                SELECT id, name, city, province
                FROM areas
                ORDER BY name
            """)
            
            areas = [dict(row) for row in results]
            
        return ApiResponse(success=True, data=areas)
        
    except Exception as e:
        logger.error(f"Get areas error: {e}")
        return ApiResponse(success=False, error=str(e))

@app.post("/api/refresh-views", response_model=ApiResponse)
async def refresh_materialized_views(db: PostgreSQLManager = Depends(get_db)):
    """Refresh materialized views for better performance"""
    try:
        await db.refresh_materialized_views()
        return ApiResponse(
            success=True,
            data={"message": "Materialized views refreshed successfully"}
        )
    except Exception as e:
        logger.error(f"Refresh views error: {e}")
        return ApiResponse(success=False, error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8787)
