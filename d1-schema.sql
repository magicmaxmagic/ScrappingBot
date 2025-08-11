-- D1 schema
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS listings (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('sale','rent')),
  price REAL NOT NULL,
  currency TEXT NOT NULL,
  url TEXT NOT NULL,
  title TEXT,
  address TEXT,
  area_sqm REAL,
  rooms REAL,
  latitude REAL,
  longitude REAL,
  neighborhood TEXT,
  site_domain TEXT,
  raw_html_path TEXT,
  extracted_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_listings_kind ON listings(kind);
CREATE INDEX IF NOT EXISTS idx_listings_price ON listings(price);
CREATE INDEX IF NOT EXISTS idx_listings_area ON listings(area_sqm);
CREATE INDEX IF NOT EXISTS idx_listings_neighborhood ON listings(neighborhood);
CREATE INDEX IF NOT EXISTS idx_listings_extracted_at ON listings(extracted_at);

CREATE TABLE IF NOT EXISTS neighborhoods (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  geojson TEXT
);

CREATE TABLE IF NOT EXISTS area_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  area_name TEXT,
  as_of TEXT,
  avg_price REAL,
  avg_price_sqm REAL,
  listing_count INTEGER
);
