-- PostgreSQL + PostGIS Schema for ScrappingBot
-- Optimized for large-scale real estate data with spatial operations

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Areas table (quartiers de Montréal avec géométries)
CREATE TABLE IF NOT EXISTS areas (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL DEFAULT 'Montreal',
    province VARCHAR(50) NOT NULL DEFAULT 'QC',
    geometry GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    area_km2 DECIMAL(10,2),
    population INTEGER,
    median_income DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name, city)
);

-- Create spatial index for fast ST_Within operations
CREATE INDEX IF NOT EXISTS idx_areas_geometry ON areas USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_areas_name ON areas(name);

-- Listings table (optimized for large volumes)
CREATE TABLE IF NOT EXISTS listings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url_hash VARCHAR(64) NOT NULL UNIQUE, -- SHA-256 hash to avoid duplicates
    url TEXT NOT NULL,
    title TEXT,
    price DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'CAD',
    price_per_sqm DECIMAL(10,2), -- Prix/m² calculé
    area_sqm DECIMAL(8,2),
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    property_type VARCHAR(50), -- condo, house, apartment
    listing_type VARCHAR(20), -- sale, rent
    address TEXT,
    coordinates GEOMETRY(POINT, 4326),
    area_id INTEGER REFERENCES areas(id), -- Detected via ST_Within
    site_domain VARCHAR(100),
    published_date DATE,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    raw_data JSONB, -- Full scraped data for AI training
    is_active BOOLEAN DEFAULT true,
    yearly_yield DECIMAL(5,2), -- Rendement annuel calculé
    monthly_rent DECIMAL(10,2) -- Loyer mensuel si location
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_listings_coordinates ON listings USING GIST(coordinates);
CREATE INDEX IF NOT EXISTS idx_listings_price ON listings(price) WHERE price > 0;
CREATE INDEX IF NOT EXISTS idx_listings_area_id ON listings(area_id);
CREATE INDEX IF NOT EXISTS idx_listings_scraped_at ON listings(scraped_at);
CREATE INDEX IF NOT EXISTS idx_listings_property_type ON listings(property_type);
CREATE INDEX IF NOT EXISTS idx_listings_listing_type ON listings(listing_type);
CREATE INDEX IF NOT EXISTS idx_listings_url_hash ON listings(url_hash);
CREATE INDEX IF NOT EXISTS idx_listings_raw_data ON listings USING GIN(raw_data);

-- Area metrics (pre-calculated statistics per quartier)
CREATE TABLE IF NOT EXISTS area_metrics (
    id SERIAL PRIMARY KEY,
    area_id INTEGER REFERENCES areas(id),
    metric_date DATE NOT NULL,
    total_listings INTEGER DEFAULT 0,
    avg_price DECIMAL(12,2),
    median_price DECIMAL(12,2),
    avg_price_per_sqm DECIMAL(10,2),
    avg_yield DECIMAL(5,2),
    total_sales INTEGER DEFAULT 0,
    total_rentals INTEGER DEFAULT 0,
    price_trend_30d DECIMAL(5,2), -- % change over 30 days
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(area_id, metric_date)
);

CREATE INDEX IF NOT EXISTS idx_area_metrics_area_date ON area_metrics(area_id, metric_date);

-- Scrape logs for monitoring and analytics
CREATE TABLE IF NOT EXISTS scrape_logs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    url TEXT,
    status VARCHAR(20) NOT NULL, -- success, blocked, error
    listings_found INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    strategy_used VARCHAR(20), -- xhr, dom
    error_message TEXT,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    raw_response_hash VARCHAR(64) -- To detect duplicate content
);

CREATE INDEX IF NOT EXISTS idx_scrape_logs_source ON scrape_logs(source);
CREATE INDEX IF NOT EXISTS idx_scrape_logs_scraped_at ON scrape_logs(scraped_at);
CREATE INDEX IF NOT EXISTS idx_scrape_logs_status ON scrape_logs(status);

-- View for quick analytics
CREATE OR REPLACE VIEW listings_with_areas AS
SELECT 
    l.*,
    a.name as area_name,
    a.city,
    a.province,
    ST_X(l.coordinates) as longitude,
    ST_Y(l.coordinates) as latitude
FROM listings l
LEFT JOIN areas a ON l.area_id = a.id;

-- Function to calculate area metrics
CREATE OR REPLACE FUNCTION refresh_area_metrics(target_date DATE DEFAULT CURRENT_DATE)
RETURNS INTEGER AS $$
DECLARE
    affected_rows INTEGER := 0;
BEGIN
    INSERT INTO area_metrics (
        area_id, 
        metric_date,
        total_listings,
        avg_price,
        median_price,
        avg_price_per_sqm,
        avg_yield,
        total_sales,
        total_rentals,
        price_trend_30d
    )
    SELECT 
        a.id as area_id,
        target_date,
        COUNT(l.id) as total_listings,
        AVG(l.price) FILTER (WHERE l.price > 0) as avg_price,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY l.price) FILTER (WHERE l.price > 0) as median_price,
        AVG(l.price_per_sqm) FILTER (WHERE l.price_per_sqm > 0) as avg_price_per_sqm,
        AVG(l.yearly_yield) FILTER (WHERE l.yearly_yield > 0) as avg_yield,
        COUNT(l.id) FILTER (WHERE l.listing_type = 'sale') as total_sales,
        COUNT(l.id) FILTER (WHERE l.listing_type = 'rent') as total_rentals,
        -- Price trend calculation (simplified)
        CASE 
            WHEN COUNT(l.id) FILTER (WHERE l.scraped_at >= target_date - INTERVAL '30 days') > 5
            THEN 0.0 -- Placeholder for trend calculation
            ELSE NULL 
        END as price_trend_30d
    FROM areas a
    LEFT JOIN listings l ON l.area_id = a.id 
        AND l.is_active = true
        AND l.scraped_at::DATE = target_date
    GROUP BY a.id
    ON CONFLICT (area_id, metric_date) DO UPDATE SET
        total_listings = EXCLUDED.total_listings,
        avg_price = EXCLUDED.avg_price,
        median_price = EXCLUDED.median_price,
        avg_price_per_sqm = EXCLUDED.avg_price_per_sqm,
        avg_yield = EXCLUDED.avg_yield,
        total_sales = EXCLUDED.total_sales,
        total_rentals = EXCLUDED.total_rentals,
        price_trend_30d = EXCLUDED.price_trend_30d;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RETURN affected_rows;
END;
$$ LANGUAGE plpgsql;

-- Function to detect area from coordinates
CREATE OR REPLACE FUNCTION detect_area_from_coordinates(lat DECIMAL, lon DECIMAL)
RETURNS INTEGER AS $$
DECLARE
    area_id INTEGER;
BEGIN
    SELECT a.id INTO area_id
    FROM areas a
    WHERE ST_Within(ST_Point(lon, lat), a.geometry)
    LIMIT 1;
    
    RETURN area_id;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically detect area and calculate metrics
CREATE OR REPLACE FUNCTION trigger_update_listing_area()
RETURNS TRIGGER AS $$
BEGIN
    -- Detect area if coordinates are provided
    IF NEW.coordinates IS NOT NULL AND NEW.area_id IS NULL THEN
        NEW.area_id := detect_area_from_coordinates(
            ST_Y(NEW.coordinates),
            ST_X(NEW.coordinates)
        );
    END IF;
    
    -- Calculate price per sqm if missing
    IF NEW.price > 0 AND NEW.area_sqm > 0 AND NEW.price_per_sqm IS NULL THEN
        NEW.price_per_sqm := NEW.price / NEW.area_sqm;
    END IF;
    
    -- Calculate yearly yield for rentals
    IF NEW.listing_type = 'rent' AND NEW.monthly_rent > 0 AND NEW.price > 0 THEN
        NEW.yearly_yield := (NEW.monthly_rent * 12 / NEW.price) * 100;
    END IF;
    
    NEW.updated_at := NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_listings_update_area
    BEFORE INSERT OR UPDATE ON listings
    FOR EACH ROW
    EXECUTE FUNCTION trigger_update_listing_area();

-- Create materialized view for faster queries
CREATE MATERIALIZED VIEW IF NOT EXISTS listings_summary AS
SELECT 
    l.area_id,
    a.name as area_name,
    COUNT(*) as total_listings,
    AVG(l.price) FILTER (WHERE l.price > 0) as avg_price,
    MIN(l.price) FILTER (WHERE l.price > 0) as min_price,
    MAX(l.price) FILTER (WHERE l.price > 0) as max_price,
    AVG(l.price_per_sqm) FILTER (WHERE l.price_per_sqm > 0) as avg_price_per_sqm,
    COUNT(*) FILTER (WHERE l.listing_type = 'sale') as sales_count,
    COUNT(*) FILTER (WHERE l.listing_type = 'rent') as rentals_count,
    DATE_TRUNC('day', MAX(l.scraped_at)) as last_updated
FROM listings l
LEFT JOIN areas a ON l.area_id = a.id
WHERE l.is_active = true
GROUP BY l.area_id, a.name;

CREATE INDEX IF NOT EXISTS idx_listings_summary_area ON listings_summary(area_id);

-- Grant permissions for application user
-- CREATE USER scraper_app WITH PASSWORD 'your_secure_password';
-- GRANT SELECT, INSERT, UPDATE ON listings, areas, area_metrics, scrape_logs TO scraper_app;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO scraper_app;
-- GRANT EXECUTE ON FUNCTION detect_area_from_coordinates TO scraper_app;
-- GRANT EXECUTE ON FUNCTION refresh_area_metrics TO scraper_app;
