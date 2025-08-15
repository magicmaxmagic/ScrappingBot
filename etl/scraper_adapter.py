"""
Scraper to ETL Adapter
======================

Adaptateur qui connecte la sortie du scraper au pipeline ETL.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess
import sys

logger = logging.getLogger(__name__)


class ScraperETLAdapter:
    """Adaptateur entre le scraper et le pipeline ETL."""
    
    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
    
    def trigger_scraping_and_etl(
        self,
        location: str = "Montreal",
        property_type: str = "condo",
        run_etl: bool = True
    ) -> Dict[str, Any]:
        """
        Déclenche le scraping puis l'ETL.
        
        Args:
            location: Localisation à scraper
            property_type: Type de propriété (condo, house, etc.)
            run_etl: Si True, lance l'ETL après le scraping
            
        Returns:
            Rapport complet de l'opération
        """
        start_time = datetime.now()
        logger.info(f"Starting scraping for {property_type} in {location}")
        
        try:
            # Étape 1: Lancer le scraping
            scraping_result = self._run_scraper(location, property_type)
            
            if not scraping_result['success']:
                return {
                    'status': 'error',
                    'error': 'Scraping failed',
                    'scraping_result': scraping_result,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Étape 2: Lancer l'ETL si demandé
            etl_result = None
            if run_etl and scraping_result.get('listings_count', 0) > 0:
                logger.info("Starting ETL pipeline")
                etl_result = self._run_etl_pipeline()
            
            # Rapport final
            total_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'total_execution_time': total_time,
                'scraping_result': scraping_result,
                'etl_result': etl_result,
                'summary': {
                    'location': location,
                    'property_type': property_type,
                    'scraped_listings': scraping_result.get('listings_count', 0),
                    'processed_listings': etl_result['summary']['processed_listings'] if etl_result else 0,
                    'loaded_to_db': etl_result['summary']['loaded_to_db'] if etl_result else 0
                }
            }
            
            logger.info(f"Scraping and ETL completed in {total_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Scraping and ETL failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'execution_time': (datetime.now() - start_time).total_seconds()
            }
    
    def _run_scraper(self, location: str, property_type: str) -> Dict[str, Any]:
        """Lance le scraper Playwright."""
        try:
            # Utiliser le script scraper existant
            scraper_script = Path(__file__).parent.parent / "database" / "scraper_adapter.py"
            
            if not scraper_script.exists():
                return {
                    'success': False,
                    'error': 'Scraper script not found',
                    'listings_count': 0
                }
            
            # Lancer le scraper
            cmd = [
                sys.executable,
                str(scraper_script),
                "--where", location,
                "--what", property_type,
                "--output", str(self.data_dir / "listings.json")
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                # Compter les résultats
                listings_file = self.data_dir / "listings.json"
                listings_count = 0
                
                if listings_file.exists():
                    try:
                        with open(listings_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            listings_count = len(data) if isinstance(data, list) else 1
                    except:
                        listings_count = 0
                
                return {
                    'success': True,
                    'listings_count': listings_count,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                return {
                    'success': False,
                    'error': f"Scraper failed with code {result.returncode}",
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'listings_count': 0
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Scraper timeout',
                'listings_count': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'listings_count': 0
            }
    
    def _run_etl_pipeline(self) -> Dict[str, Any]:
        """Lance le pipeline ETL."""
        try:
            etl_script = Path(__file__).parent / "orchestrator.py"
            
            cmd = [
                sys.executable,
                str(etl_script),
                "--full",
                "--input", "listings.json"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                # Parser la sortie JSON
                try:
                    etl_result = json.loads(result.stdout)
                    return etl_result
                except json.JSONDecodeError:
                    return {
                        'status': 'success',
                        'note': 'ETL completed but output not parseable',
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    }
            else:
                return {
                    'status': 'error',
                    'error': f"ETL failed with code {result.returncode}",
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'error': 'ETL timeout'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def schedule_regular_scraping(self, locations: List[str], property_types: List[str]) -> Dict[str, Any]:
        """Planifie un scraping régulier pour plusieurs localisations/types."""
        results = []
        total_listings = 0
        total_processed = 0
        total_loaded = 0
        
        start_time = datetime.now()
        
        for location in locations:
            for prop_type in property_types:
                logger.info(f"Processing {prop_type} in {location}")
                
                result = self.trigger_scraping_and_etl(location, prop_type, run_etl=True)
                results.append({
                    'location': location,
                    'property_type': prop_type,
                    'result': result
                })
                
                if result['status'] == 'success':
                    summary = result.get('summary', {})
                    total_listings += summary.get('scraped_listings', 0)
                    total_processed += summary.get('processed_listings', 0)
                    total_loaded += summary.get('loaded_to_db', 0)
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'total_execution_time': total_time,
            'summary': {
                'total_jobs': len(locations) * len(property_types),
                'total_scraped': total_listings,
                'total_processed': total_processed,
                'total_loaded': total_loaded
            },
            'detailed_results': results
        }


def main():
    """Point d'entrée pour tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scraper ETL Adapter")
    parser.add_argument('--where', default='Montreal', help='Location to scrape')
    parser.add_argument('--what', default='condo', help='Property type to scrape')
    parser.add_argument('--no-etl', action='store_true', help='Skip ETL pipeline')
    
    args = parser.parse_args()
    
    adapter = ScraperETLAdapter()
    result = adapter.trigger_scraping_and_etl(
        location=args.where,
        property_type=args.what,
        run_etl=not args.no_etl
    )
    
    print(json.dumps(result, indent=2, default=str))
    return 0 if result['status'] == 'success' else 1


if __name__ == "__main__":
    exit(main())
