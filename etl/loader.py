"""
Data Loader pour PostgreSQL + PostGIS
=====================================

Charge les données nettoyées dans la base de données PostgreSQL.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import os

logger = logging.getLogger(__name__)


class PostgreSQLLoader:
    """Chargeur de données pour PostgreSQL + PostGIS."""
    
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or os.getenv(
            'DATABASE_URL',
            'postgresql://scrappingbot_user:scrappingbot_password@localhost:5432/scrappingbot'
        )
        self.connection = None
    
    def connect(self) -> bool:
        """Établit la connexion à la base de données."""
        try:
            self.connection = psycopg2.connect(self.connection_string)
            self.connection.autocommit = False
            logger.info("Connected to PostgreSQL database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Ferme la connexion à la base de données."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def ensure_tables_exist(self) -> bool:
        """S'assure que les tables nécessaires existent."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS listings (
            id SERIAL PRIMARY KEY,
            hash VARCHAR(32) UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            price DECIMAL(12,2),
            area DECIMAL(8,2),
            bedrooms INTEGER,
            bathrooms DECIMAL(3,1),
            address TEXT,
            neighborhood TEXT,
            city TEXT DEFAULT 'Montreal',
            province TEXT DEFAULT 'QC',
            postal_code VARCHAR(7),
            property_type TEXT,
            listing_type TEXT DEFAULT 'sale',
            url TEXT UNIQUE NOT NULL,
            source TEXT DEFAULT 'scraper',
            scraped_at TIMESTAMP DEFAULT NOW(),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            latitude DECIMAL(10,8),
            longitude DECIMAL(11,8),
            location GEOMETRY(Point, 4326),
            images JSONB DEFAULT '[]'::jsonb,
            features JSONB DEFAULT '[]'::jsonb,
            is_active BOOLEAN DEFAULT true
        );

        -- Index pour les performances
        CREATE INDEX IF NOT EXISTS idx_listings_hash ON listings(hash);
        CREATE INDEX IF NOT EXISTS idx_listings_price ON listings(price) WHERE price IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_listings_area ON listings(area) WHERE area IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_listings_city ON listings(city);
        CREATE INDEX IF NOT EXISTS idx_listings_property_type ON listings(property_type);
        CREATE INDEX IF NOT EXISTS idx_listings_scraped_at ON listings(scraped_at);
        CREATE INDEX IF NOT EXISTS idx_listings_active ON listings(is_active) WHERE is_active = true;
        
        -- Index spatial pour PostGIS
        CREATE INDEX IF NOT EXISTS idx_listings_location ON listings USING GIST(location) WHERE location IS NOT NULL;
        
        -- Trigger pour mettre à jour updated_at
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        DROP TRIGGER IF EXISTS update_listings_updated_at ON listings;
        CREATE TRIGGER update_listings_updated_at 
            BEFORE UPDATE ON listings 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
        
        -- Trigger pour créer le point géométrique
        CREATE OR REPLACE FUNCTION update_location_from_coords()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
                NEW.location = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
            END IF;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        DROP TRIGGER IF EXISTS update_listings_location ON listings;
        CREATE TRIGGER update_listings_location 
            BEFORE INSERT OR UPDATE ON listings 
            FOR EACH ROW 
            EXECUTE FUNCTION update_location_from_coords();
        """
        
        try:
            if not self.connection:
                logger.error("No database connection available.")
                return False
            with self.connection.cursor() as cursor:
                cursor.execute(create_table_sql)
                self.connection.commit()
                logger.info("Database tables ensured")
                return True
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def upsert_listings(self, listings: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Insert ou update des annonces.
        
        Returns:
            Tuple (inserted_count, updated_count)
        """
        if not listings:
            return 0, 0
        
        inserted_count = 0
        updated_count = 0
        
        upsert_sql = """
        INSERT INTO listings (
            hash, title, description, price, area, bedrooms, bathrooms,
            address, neighborhood, city, province, postal_code,
            property_type, listing_type, url, source, scraped_at,
            latitude, longitude, images, features
        ) VALUES %s
        ON CONFLICT (hash) 
        DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            price = EXCLUDED.price,
            area = EXCLUDED.area,
            bedrooms = EXCLUDED.bedrooms,
            bathrooms = EXCLUDED.bathrooms,
            address = EXCLUDED.address,
            neighborhood = EXCLUDED.neighborhood,
            city = EXCLUDED.city,
            province = EXCLUDED.province,
            postal_code = EXCLUDED.postal_code,
            property_type = EXCLUDED.property_type,
            listing_type = EXCLUDED.listing_type,
            url = EXCLUDED.url,
            source = EXCLUDED.source,
            scraped_at = EXCLUDED.scraped_at,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            images = EXCLUDED.images,
            features = EXCLUDED.features,
            updated_at = NOW(),
            is_active = true
        RETURNING (xmax = 0) AS inserted;
        """
        
        # Préparer les données
        values = []
        for listing in listings:
            values.append((
                listing.get('hash'),
                listing.get('title'),
                listing.get('description'),
                listing.get('price'),
                listing.get('area'),
                listing.get('bedrooms'),
                listing.get('bathrooms'),
                listing.get('address'),
                listing.get('neighborhood'),
                listing.get('city', 'Montreal'),
                listing.get('province', 'QC'),
                listing.get('postal_code'),
                listing.get('property_type'),
                listing.get('listing_type', 'sale'),
                listing.get('url'),
                listing.get('source', 'scraper'),
                listing.get('scraped_at', datetime.now()),
                listing.get('latitude'),
                listing.get('longitude'),
                json.dumps(listing.get('images', [])),
                json.dumps(listing.get('features', []))
            ))
        
        try:
            if not self.connection:
                raise Exception("Database connection is not established.")
            with self.connection.cursor() as cursor:
                cursor.execute("BEGIN;")
                
                # Exécuter l'upsert
                execute_values(
                    cursor,
                    upsert_sql,
                    values,
                    template=None,
                    page_size=100
                )
                
                # Compter les insertions et mises à jour
                results = cursor.fetchall()
                for result in results:
                    if result[0]:  # inserted = True
                        inserted_count += 1
                    else:  # updated
                        updated_count += 1
                
                self.connection.commit()
                logger.info(f"Loaded {len(listings)} listings: {inserted_count} inserted, {updated_count} updated")
                
        except Exception as e:
            logger.error(f"Failed to load listings: {e}")
            if self.connection:
                self.connection.rollback()
            raise
        
        return inserted_count, updated_count
    
    def mark_stale_listings(self, max_age_hours: int = 24) -> int:
        """Marque les anciennes annonces comme inactives."""
        sql = """
        UPDATE listings 
        SET is_active = false, updated_at = NOW()
        WHERE is_active = true 
        AND scraped_at < NOW() - INTERVAL '%s hours'
        RETURNING id;
        """
        
        try:
            if not self.connection:
                logger.error("No database connection available.")
                return 0
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (max_age_hours,))
                count = cursor.rowcount
                self.connection.commit()
                logger.info(f"Marked {count} listings as inactive")
                return count
        except Exception as e:
            logger.error(f"Failed to mark stale listings: {e}")
            if self.connection:
                self.connection.rollback()
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques de la base de données."""
        stats_sql = """
        SELECT 
            COUNT(*) as total_listings,
            COUNT(*) FILTER (WHERE is_active = true) as active_listings,
            COUNT(*) FILTER (WHERE scraped_at::date = CURRENT_DATE) as today_listings,
            AVG(price) FILTER (WHERE price IS NOT NULL AND is_active = true) as avg_price,
            COUNT(DISTINCT city) as cities_count,
            COUNT(DISTINCT property_type) as property_types_count,
            MAX(scraped_at) as last_scrape,
            COUNT(*) FILTER (WHERE latitude IS NOT NULL AND longitude IS NOT NULL) as geocoded_listings
        FROM listings;
        """
        
        try:
            if not self.connection:
                logger.error("No database connection available.")
                return {}
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(stats_sql)
                row = cursor.fetchone()
                if row is None:
                    return {}
                stats = dict(row)
                
                # Formatage des résultats
                if stats['avg_price']:
                    stats['avg_price'] = float(stats['avg_price'])
                if stats['last_scrape']:
                    stats['last_scrape'] = stats['last_scrape'].isoformat()
                
                return stats
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Supprime les anciennes données inactives."""
        sql = """
        DELETE FROM listings 
        WHERE is_active = false 
        AND updated_at < NOW() - INTERVAL '%s days';
        """
        
        try:
            if not self.connection:
                logger.error("No database connection available.")
                return 0
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (days_to_keep,))
                count = cursor.rowcount
                self.connection.commit()
                logger.info(f"Deleted {count} old inactive listings")
                return count
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            if self.connection:
                self.connection.rollback()
            return 0


def load_data_to_db(
    input_file: str = "cleaned_listings.json",
    mark_stale_hours: int = 24,
    cleanup_days: int = 30
) -> Dict[str, Any]:
    """
    Charge les données nettoyées dans PostgreSQL.
    
    Args:
        input_file: Fichier JSON contenant les données nettoyées
        mark_stale_hours: Heures après lesquelles marquer les annonces comme inactives
        cleanup_days: Jours après lesquels supprimer les données inactives
    
    Returns:
        Rapport de chargement
    """
    start_time = datetime.now()
    loader = PostgreSQLLoader()
    
    try:
        # Connexion
        if not loader.connect():
            raise Exception("Failed to connect to database")
        
        # Créer les tables si nécessaire
        if not loader.ensure_tables_exist():
            raise Exception("Failed to ensure tables exist")
        
        # Charger les données
        input_path = Path("data") / input_file
        if not input_path.exists():
            raise FileNotFoundError(f"Input file {input_path} not found")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            listings = json.load(f)
        
        if not listings:
            logger.warning("No data to load")
            return {
                'status': 'success',
                'message': 'No data to load',
                'stats': {'loaded': 0, 'inserted': 0, 'updated': 0}
            }
        
        # Charger les données
        inserted, updated = loader.upsert_listings(listings)
        
        # Marquer les anciennes annonces comme inactives
        stale_count = loader.mark_stale_listings(mark_stale_hours)
        
        # Nettoyage des anciennes données
        cleanup_count = loader.cleanup_old_data(cleanup_days)
        
        # Statistiques
        db_stats = loader.get_statistics()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        report = {
            'status': 'success',
            'stats': {
                'loaded': len(listings),
                'inserted': inserted,
                'updated': updated,
                'marked_stale': stale_count,
                'cleaned_up': cleanup_count
            },
            'database_stats': db_stats,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Data loading completed in {execution_time:.2f}s")
        return report
        
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
    finally:
        loader.disconnect()


if __name__ == "__main__":
    result = load_data_to_db()
    print(json.dumps(result, indent=2))
