-- Cloudflare D1 / SQLite DDL for listings table
CREATE TABLE IF NOT EXISTS listings (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
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
  extracted_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_listings_url ON listings(url);
CREATE INDEX IF NOT EXISTS idx_listings_price ON listings(price);
