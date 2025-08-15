#!/usr/bin/env python3
"""
Automated Scheduler Service for ScrappingBot
Handles periodic scraping tasks and maintenance
"""

import os
import yaml
import json
import logging
import asyncio
import schedule
import time
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://scrappingbot_user:scrappingbot_pass@postgres:5432/scrappingbot')
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')
SCRAPER_API_URL = os.getenv('SCRAPER_API_URL', 'http://scraper:8000')

class SchedulerService:
    """Automated scraping scheduler"""
    
    def __init__(self, config_file: str = '/app/config/scheduler.yml'):
        self.config_file = config_file
        self.config = self.load_config()
        self.running = False
        
    def load_config(self) -> Dict:
        """Load scheduler configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    logger.info(f"Loaded config from {self.config_file}")
                    return config
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
        
        # Default configuration
        return {
            'scraping_jobs': [
                {
                    'name': 'montreal_condos',
                    'where': 'Montreal',
                    'what': 'condo',
                    'schedule': 'hourly',
                    'enabled': True
                },
                {
                    'name': 'montreal_houses',
                    'where': 'Montreal', 
                    'what': 'house',
                    'schedule': '4hours',
                    'enabled': True
                },
                {
                    'name': 'downtown_condos',
                    'where': 'Downtown Montreal',
                    'what': 'condo',
                    'schedule': '2hours',
                    'enabled': True
                }
            ],
            'maintenance_jobs': [
                {
                    'name': 'refresh_views',
                    'schedule': 'daily',
                    'enabled': True
                },
                {
                    'name': 'cleanup_old_logs',
                    'schedule': 'weekly',
                    'enabled': True
                }
            ]
        }
    
    async def run_scraping_job(self, job: Dict):
        """Execute a scraping job"""
        job_name = job['name']
        logger.info(f"Starting scraping job: {job_name}")
        
        try:
            # Use the enhanced scraper directly
            import sys
            sys.path.append('/app')
            from database.scraper_adapter import EnhancedRealEstateScraper
            
            async with EnhancedRealEstateScraper(
                headless=True,
                use_postgres=True
            ) as scraper:
                result = await scraper.scrape(
                    where=job['where'],
                    what=job['what'],
                    when='all',
                    source=job_name
                )
                
                if result.get('success'):
                    logger.info(f"Job {job_name} completed: {result.get('count')} listings")
                else:
                    logger.error(f"Job {job_name} failed: {result.get('error')}")
                    
        except Exception as e:
            logger.error(f"Job {job_name} exception: {e}")
    
    async def refresh_materialized_views(self):
        """Refresh PostgreSQL materialized views"""
        try:
            from database.postgres_manager import PostgreSQLManager
            
            db = PostgreSQLManager(DATABASE_URL)
            await db.init_pool()
            await db.refresh_materialized_views()
            await db.close_pool()
            
            logger.info("Materialized views refreshed")
            
        except Exception as e:
            logger.error(f"Failed to refresh views: {e}")
    
    async def cleanup_old_logs(self):
        """Clean up old log files"""
        try:
            logs_dir = Path('/app/logs')
            if not logs_dir.exists():
                return
            
            cutoff_date = datetime.now() - timedelta(days=7)
            cleaned = 0
            
            for log_file in logs_dir.glob('*.log'):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    cleaned += 1
            
            logger.info(f"Cleaned up {cleaned} old log files")
            
        except Exception as e:
            logger.error(f"Log cleanup failed: {e}")
    
    def schedule_jobs(self):
        """Schedule all jobs"""
        # Schedule scraping jobs
        for job in self.config.get('scraping_jobs', []):
            if not job.get('enabled'):
                continue
                
            job_name = job['name']
            schedule_type = job['schedule']
            
            if schedule_type == 'hourly':
                schedule.every().hour.do(self.run_job, job, 'scraping')
            elif schedule_type == '2hours':
                schedule.every(2).hours.do(self.run_job, job, 'scraping')
            elif schedule_type == '4hours':
                schedule.every(4).hours.do(self.run_job, job, 'scraping')
            elif schedule_type == 'daily':
                schedule.every().day.at("06:00").do(self.run_job, job, 'scraping')
            
            logger.info(f"Scheduled scraping job: {job_name} ({schedule_type})")
        
        # Schedule maintenance jobs
        for job in self.config.get('maintenance_jobs', []):
            if not job.get('enabled'):
                continue
                
            job_name = job['name']
            schedule_type = job['schedule']
            
            if schedule_type == 'daily':
                if job_name == 'refresh_views':
                    schedule.every().day.at("02:00").do(self.run_job, job, 'maintenance')
                else:
                    schedule.every().day.at("03:00").do(self.run_job, job, 'maintenance')
            elif schedule_type == 'weekly':
                schedule.every().sunday.at("01:00").do(self.run_job, job, 'maintenance')
            
            logger.info(f"Scheduled maintenance job: {job_name} ({schedule_type})")
    
    def run_job(self, job: Dict, job_type: str):
        """Run a job (sync wrapper for async functions)"""
        try:
            if job_type == 'scraping':
                asyncio.create_task(self.run_scraping_job(job))
            elif job_type == 'maintenance':
                if job['name'] == 'refresh_views':
                    asyncio.create_task(self.refresh_materialized_views())
                elif job['name'] == 'cleanup_old_logs':
                    asyncio.create_task(self.cleanup_old_logs())
        except Exception as e:
            logger.error(f"Failed to run job {job['name']}: {e}")
    
    async def health_check(self):
        """Periodic health check"""
        try:
            # Check database connection
            from database.postgres_manager import PostgreSQLManager
            db = PostgreSQLManager(DATABASE_URL)
            await db.init_pool()
            stats = await db.get_stats()
            await db.close_pool()
            
            logger.info(f"Health check: {stats.get('total_listings', 0)} listings in database")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    async def run(self):
        """Main scheduler loop"""
        logger.info("Starting ScrappingBot Scheduler")
        
        # Schedule all jobs
        self.schedule_jobs()
        
        # Schedule health checks every 10 minutes
        schedule.every(10).minutes.do(lambda: asyncio.create_task(self.health_check()))
        
        # Log startup info
        logger.info(f"Scheduler started with {len(schedule.jobs)} jobs")
        for job in schedule.jobs:
            logger.info(f"  - {job}")
        
        self.running = True
        
        # Main loop
        while self.running:
            try:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                self.running = False
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)
        
        logger.info("Scheduler stopped")

async def main():
    """Entry point"""
    scheduler = SchedulerService()
    await scheduler.run()

if __name__ == "__main__":
    asyncio.run(main())
