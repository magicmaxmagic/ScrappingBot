# PostgreSQL + PostGIS Integration Guide

ScrappingBot now supports PostgreSQL with PostGIS extension for large-scale spatial real estate data management.

## Features

- **Spatial Operations**: GeoJSON area detection, coordinate-based filtering, ST_Within queries
- **Scalable Storage**: Handle millions of listings with optimized indexes
- **Deduplication**: Hash-based URL deduplication prevents duplicates
- **Area Management**: Montreal neighborhoods with polygon boundaries
- **API Integration**: Cloudflare Workers API with PostgreSQL connection
- **Real-time Dashboard**: React frontend with spatial filtering

## Quick Start

### 1. Database Setup

```bash
# Install dependencies and initialize database
python database/setup.py --all

# Or step by step:
python database/setup.py --install-deps
python database/setup.py --create-env
python database/setup.py --init
python database/setup.py --load-areas data/montreal-areas.geojson
python database/setup.py --verify
```

### 2. Configure Environment

Edit `.env` file:

```env
# PostgreSQL Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/scrappingbot

# For Supabase (recommended for production)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres

# API Configuration
VITE_API_URL=http://localhost:8787
CORS_ORIGIN=http://localhost:5173
```

### 3. Run Enhanced Scraper

```bash
# Scrape with PostgreSQL integration
python database/scraper_adapter.py --where Montreal --what condo

# Force JSON-only mode
python database/scraper_adapter.py --where Montreal --what house --no-postgres
```

### 4. Start API Worker

```bash
cd workers/postgres-api
npm install
wrangler secret put DATABASE_URL  # Your PostgreSQL connection string
npm run dev
```

### 5. Launch Frontend

```bash
cd frontend
npm install
npm run dev
```

## Architecture

### Database Schema

```sql
-- Areas (neighborhoods with geometry)
CREATE TABLE areas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    province VARCHAR(10) DEFAULT 'QC',
    geometry GEOMETRY(MULTIPOLYGON, 4326),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Listings with spatial data
CREATE TABLE listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url_hash CHAR(64) UNIQUE NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    price DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'CAD',
    coordinates GEOMETRY(POINT, 4326),
    area_id UUID REFERENCES areas(id),
    raw_data JSONB,
    scraped_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);
```

### Component Integration

1. **PostgreSQLManager** (`database/postgres_manager.py`)
   - Connection pooling with asyncpg
   - Spatial operations with PostGIS
   - Area detection and assignment

2. **ScraperAdapter** (`database/scraper_adapter.py`)
   - Extends existing scraper
   - Converts data to PostgreSQL format
   - Maintains JSON preview compatibility

3. **Cloudflare Worker** (`workers/postgres-api/`)
   - REST API endpoints
   - Spatial filtering (bounding box, areas)
   - Real-time statistics

4. **React Frontend** (Enhanced)
   - PostgreSQL data integration
   - Spatial filters and map interactions
   - Area-based statistics panel

## Spatial Operations

### Area Detection

```python
# Assign listings to areas based on coordinates
await db.assign_areas_to_listings()

# Find listings within an area
listings = await db.get_listings_by_area("Plateau Mont-Royal")
```

### Bounding Box Queries

```python
# Get listings within map bounds
listings = await db.get_listings_in_polygon([
    (-73.6, 45.5),   # Southwest
    (-73.5, 45.5),   # Southeast  
    (-73.5, 45.6),   # Northeast
    (-73.6, 45.6)    # Northwest
])
```

### API Endpoints

```bash
# Get listings with filters
GET /api/listings?area=Plateau&min_price=300000&max_price=600000

# Get listings within map bounds
GET /api/listings?bbox=-73.6,45.5,-73.5,45.6

# Get area statistics
GET /api/areas/stats

# Get recent activity
GET /api/activity
```

## Migration from D1

### 1. Export Existing D1 Data

```bash
# Export D1 data to JSON
wrangler d1 execute scrappingbot --command="SELECT * FROM listings" --output=json > d1_export.json
```

### 2. Import to PostgreSQL

```python
import json
import asyncio
from database.postgres_manager import PostgreSQLManager, ListingData

async def migrate_d1_data():
    db = PostgreSQLManager()
    await db.init_pool()
    
    with open('d1_export.json', 'r') as f:
        d1_data = json.load(f)
    
    for item in d1_data['results']:
        listing = ListingData(
            url=item['url'],
            title=item['title'],
            price=item['price'],
            # ... convert other fields
        )
        await db.upsert_listing(listing)
    
    await db.close_pool()

# Run migration
asyncio.run(migrate_d1_data())
```

## Performance Optimization

### Indexes

The schema includes optimized indexes for:

- Spatial queries: `GIST(geometry)` and `GIST(coordinates)`
- Deduplication: `UNIQUE(url_hash)`
- Area queries: `btree(area_id, is_active)`
- Time-based queries: `btree(scraped_at DESC)`

### Connection Pooling

```python
# Configure connection pool
db = PostgreSQLManager()
await db.init_pool()  # 2-10 connections

# Use connection context manager
async with db.get_connection() as conn:
    results = await conn.fetch("SELECT * FROM listings LIMIT 10")
```

### Materialized Views

```sql
-- Pre-computed area statistics
CREATE MATERIALIZED VIEW listings_summary AS
SELECT 
    area_id,
    COUNT(*) as listing_count,
    AVG(price) as avg_price,
    MAX(scraped_at) as latest_scrape
FROM listings 
WHERE is_active = true 
GROUP BY area_id;

-- Refresh periodically
REFRESH MATERIALIZED VIEW CONCURRENTLY listings_summary;
```

## Deployment

### Local Development

1. PostgreSQL with PostGIS extension
2. Python environment with asyncpg
3. Node.js for Workers and Frontend

### Production Options

**Option 1: Supabase (Recommended)**
- Managed PostgreSQL with PostGIS
- Built-in API and real-time features
- Edge functions for Workers
- Free tier available

**Option 2: Neon**
- Serverless PostgreSQL
- Excellent performance
- PostGIS support

**Option 3: Self-hosted**
- PostgreSQL 12+ with PostGIS 3+
- Connection pooling (PgBouncer)
- Regular backups

### Environment Variables

```bash
# Production secrets
wrangler secret put DATABASE_URL
wrangler secret put CORS_ORIGIN

# Development
export DATABASE_URL="postgresql://..."
export VITE_API_URL="https://your-worker.workers.dev"
```

## Monitoring

### Database Health

```bash
# Check connection and stats
python database/postgres_manager.py --stats

# Refresh materialized views
python database/postgres_manager.py --refresh-views
```

### Scraping Metrics

The system logs all scraping attempts:

```sql
SELECT 
    source,
    status,
    COUNT(*) as attempts,
    AVG(response_time_ms) as avg_response_time,
    SUM(listings_found) as total_listings
FROM scrape_logs 
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY source, status;
```

## Troubleshooting

### Connection Issues

```python
# Test basic connectivity
import asyncpg

async def test_connection():
    conn = await asyncpg.connect("postgresql://...")
    result = await conn.fetchrow("SELECT version()")
    print(result['version'])
    await conn.close()
```

### PostGIS Extension

```sql
-- Check PostGIS installation
SELECT PostGIS_Version();

-- Enable PostGIS if not available
CREATE EXTENSION IF NOT EXISTS postgis;
```

### Performance Issues

1. **Check query plans**: `EXPLAIN ANALYZE SELECT ...`
2. **Monitor connections**: `SELECT * FROM pg_stat_activity`
3. **Update statistics**: `ANALYZE listings;`
4. **Reindex if needed**: `REINDEX INDEX CONCURRENTLY idx_listings_coordinates`

---

This PostgreSQL integration maintains full compatibility with existing JSON workflows while adding enterprise-scale spatial capabilities and real-time data management.
