#!/usr/bin/env python3
"""
PostgreSQL Setup and Migration Script for ScrappingBot
Handles database initialization, schema migration, and area data loading
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database.postgres_manager import PostgreSQLManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostgreSQLSetup:
    """Handles PostgreSQL setup and migrations"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.db_manager = PostgreSQLManager()
        
    async def check_postgresql_available(self) -> bool:
        """Check if PostgreSQL is available"""
        try:
            await self.db_manager.init_pool()
            async with self.db_manager.get_connection() as conn:
                result = await conn.fetchrow("SELECT version()")
                logger.info(f"PostgreSQL available: {result['version']}")
                return True
        except Exception as e:
            logger.error(f"PostgreSQL not available: {e}")
            return False
        finally:
            if self.db_manager.pool:
                await self.db_manager.close_pool()
    
    async def run_schema_migration(self, schema_file: str = "database/schema.sql") -> bool:
        """Run schema migration"""
        schema_path = self.project_root / schema_file
        
        if not schema_path.exists():
            logger.error(f"Schema file not found: {schema_path}")
            return False
        
        try:
            logger.info("Running schema migration...")
            
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            await self.db_manager.init_pool()
            async with self.db_manager.get_connection() as conn:
                await conn.execute(schema_sql)
            
            logger.info("Schema migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Schema migration failed: {e}")
            return False
        finally:
            if self.db_manager.pool:
                await self.db_manager.close_pool()
    
    async def load_montreal_areas(self, geojson_file: Optional[str] = None) -> bool:
        """Load Montreal area data from GeoJSON"""
        if not geojson_file:
            # Look for GeoJSON files in data directory
            data_dir = self.project_root / "data"
            geojson_files = list(data_dir.glob("*.geojson")) + list(data_dir.glob("*.json"))
            
            if geojson_files:
                geojson_file = str(geojson_files[0])
                logger.info(f"Found GeoJSON file: {geojson_file}")
            else:
                logger.warning("No GeoJSON file specified and none found in data/ directory")
                return False
        
        try:
            await self.db_manager.init_pool()
            count = await self.db_manager.load_montreal_areas(geojson_file)
            logger.info(f"Loaded {count} areas from {geojson_file}")
            return count > 0
            
        except Exception as e:
            logger.error(f"Failed to load areas: {e}")
            return False
        finally:
            if self.db_manager.pool:
                await self.db_manager.close_pool()
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies for PostgreSQL"""
        requirements_file = self.project_root / "database" / "requirements.txt"
        
        if not requirements_file.exists():
            logger.warning("Database requirements.txt not found, skipping dependency install")
            return True
        
        try:
            logger.info("Installing PostgreSQL dependencies...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], check=True, capture_output=True, text=True)
            
            logger.info("Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e.stderr}")
            return False
    
    def create_env_template(self):
        """Create .env template for PostgreSQL configuration"""
        env_template_path = self.project_root / ".env.postgresql.template"
        
        env_template = """# PostgreSQL Configuration for ScrappingBot
# Copy to .env and configure your database connection

# For local PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=scrappingbot

# Or use a complete DATABASE_URL (takes precedence)
# DATABASE_URL=postgresql://user:password@host:port/database

# For Supabase
# DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# For Neon
# DATABASE_URL=postgresql://[user]:[password]@[neon_hostname]/[dbname]?sslmode=require

# API Configuration
VITE_API_URL=http://localhost:8787
CORS_ORIGIN=http://localhost:5173
"""
        
        try:
            with open(env_template_path, 'w') as f:
                f.write(env_template)
            logger.info(f"Environment template created: {env_template_path}")
            
            # Also create a basic .env if it doesn't exist
            env_path = self.project_root / ".env"
            if not env_path.exists():
                with open(env_path, 'w') as f:
                    f.write("# Configure your PostgreSQL connection here\n")
                    f.write("DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scrappingbot\n")
                logger.info("Basic .env file created")
                
        except Exception as e:
            logger.error(f"Failed to create env template: {e}")
    
    async def verify_setup(self) -> bool:
        """Verify that PostgreSQL setup is working"""
        try:
            await self.db_manager.init_pool()
            
            # Test basic operations
            stats = await self.db_manager.get_stats()
            logger.info(f"Database stats: {stats}")
            
            # Test areas table
            async with self.db_manager.get_connection() as conn:
                result = await conn.fetchrow("SELECT COUNT(*) as count FROM areas")
                area_count = result['count']
                logger.info(f"Areas loaded: {area_count}")
            
            if area_count == 0:
                logger.warning("No areas loaded - consider running with --load-areas")
            
            logger.info("✅ PostgreSQL setup verification completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup verification failed: {e}")
            return False
        finally:
            if self.db_manager.pool:
                await self.db_manager.close_pool()

async def main():
    """Setup PostgreSQL for ScrappingBot"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PostgreSQL Setup for ScrappingBot")
    parser.add_argument('--init', action='store_true', help='Initialize database schema')
    parser.add_argument('--load-areas', help='Load area data from GeoJSON file')
    parser.add_argument('--install-deps', action='store_true', help='Install Python dependencies')
    parser.add_argument('--create-env', action='store_true', help='Create environment template')
    parser.add_argument('--verify', action='store_true', help='Verify setup')
    parser.add_argument('--all', action='store_true', help='Run complete setup')
    
    args = parser.parse_args()
    
    setup = PostgreSQLSetup()
    success = True
    
    # Run complete setup
    if args.all:
        logger.info("🚀 Starting complete PostgreSQL setup...")
        
        # Install dependencies
        if not setup.install_dependencies():
            success = False
        
        # Create environment template
        setup.create_env_template()
        
        # Check PostgreSQL availability
        if not await setup.check_postgresql_available():
            logger.error("❌ PostgreSQL not available. Please check your connection configuration.")
            success = False
        else:
            # Initialize schema
            if not await setup.run_schema_migration():
                success = False
            
            # Load areas if possible
            if await setup.load_montreal_areas():
                logger.info("✅ Areas loaded successfully")
            
            # Verify setup
            if not await setup.verify_setup():
                success = False
    
    # Individual operations
    else:
        if args.install_deps:
            if not setup.install_dependencies():
                success = False
        
        if args.create_env:
            setup.create_env_template()
        
        if args.init:
            if not await setup.check_postgresql_available():
                success = False
            elif not await setup.run_schema_migration():
                success = False
        
        if args.load_areas:
            if not await setup.load_montreal_areas(args.load_areas):
                success = False
        
        if args.verify:
            if not await setup.verify_setup():
                success = False
    
    if success:
        logger.info("✅ Setup completed successfully!")
        print("\n🎉 PostgreSQL setup complete!")
        print("\nNext steps:")
        print("1. Configure your database connection in .env")
        print("2. Test the enhanced scraper: python database/scraper_adapter.py --where Montreal --what condo")
        print("3. Start the API worker: cd workers/postgres-api && npm run dev")
        print("4. Start the frontend: cd frontend && npm run dev")
    else:
        logger.error("❌ Setup failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
