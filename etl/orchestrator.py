"""
ETL Orchestrator pour ScrappingBot
=================================

Orchestre le pipeline ETL complet : Extract -> Transform -> Load
"""

import sys
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ajout du répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from etl import run_etl_pipeline
from etl.loader import load_data_to_db


class ETLOrchestrator:
    """Orchestrateur du pipeline ETL complet."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
    def run_full_pipeline(
        self,
        input_file: str = "listings.json",
        mark_stale_hours: int = 24,
        cleanup_days: int = 30
    ) -> Dict[str, Any]:
        """
        Exécute le pipeline ETL complet.
        
        Args:
            input_file: Fichier d'entrée avec les données scrapées
            mark_stale_hours: Heures avant de marquer les données comme obsolètes
            cleanup_days: Jours avant de supprimer les données inactives
            
        Returns:
            Rapport complet de l'exécution
        """
        start_time = datetime.now()
        logger.info("Starting complete ETL pipeline")
        
        try:
            # Étape 1: ETL (Extract, Transform, Validate)
            logger.info("Step 1: Running ETL pipeline (Extract, Transform, Validate)")
            etl_report = run_etl_pipeline(
                input_file=input_file,
                output_file="cleaned_listings.json"
            )
            
            if etl_report['status'] != 'success':
                raise Exception("ETL pipeline failed")
            
            # Étape 2: Load vers PostgreSQL
            logger.info("Step 2: Loading data to PostgreSQL")
            load_report = load_data_to_db(
                input_file="cleaned_listings.json",
                mark_stale_hours=mark_stale_hours,
                cleanup_days=cleanup_days
            )
            
            if load_report['status'] != 'success':
                raise Exception(f"Data loading failed: {load_report.get('error', 'Unknown error')}")
            
            # Rapport final
            total_time = (datetime.now() - start_time).total_seconds()
            
            final_report = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'total_execution_time': total_time,
                'etl_pipeline': etl_report,
                'data_loading': load_report,
                'summary': {
                    'raw_listings': etl_report['stats']['extracted'],
                    'processed_listings': etl_report['stats']['valid'],
                    'loaded_to_db': load_report['stats']['loaded'],
                    'db_insertions': load_report['stats']['inserted'],
                    'db_updates': load_report['stats']['updated']
                }
            }
            
            # Sauvegarder le rapport final
            report_path = self.data_dir / "etl_full_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(final_report, f, indent=2, default=str)
            
            logger.info(f"Complete ETL pipeline finished in {total_time:.2f}s")
            logger.info(f"Summary: {final_report['summary']}")
            
            return final_report
            
        except Exception as e:
            error_report = {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'execution_time': (datetime.now() - start_time).total_seconds()
            }
            
            logger.error(f"ETL pipeline failed: {e}")
            
            # Sauvegarder le rapport d'erreur
            error_path = self.data_dir / "etl_error_report.json"
            with open(error_path, 'w', encoding='utf-8') as f:
                json.dump(error_report, f, indent=2, default=str)
            
            return error_report
    
    def run_transform_only(self, input_file: str = "listings.json") -> Dict[str, Any]:
        """Exécute seulement la partie transformation."""
        logger.info("Running transform-only pipeline")
        return run_etl_pipeline(input_file, "cleaned_listings.json")
    
    def run_load_only(
        self,
        input_file: str = "cleaned_listings.json",
        mark_stale_hours: int = 24,
        cleanup_days: int = 30
    ) -> Dict[str, Any]:
        """Exécute seulement le chargement en base."""
        logger.info("Running load-only pipeline")
        return load_data_to_db(input_file, mark_stale_hours, cleanup_days)


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="ETL Orchestrator for ScrappingBot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --full                           # Run complete pipeline
  %(prog)s --transform-only                 # Only transform data
  %(prog)s --load-only                      # Only load to database
  %(prog)s --input custom.json --full       # Use custom input file
  %(prog)s --full --mark-stale 48           # Mark data as stale after 48h
        """
    )
    
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run the complete ETL pipeline (default)'
    )
    
    parser.add_argument(
        '--transform-only',
        action='store_true',
        help='Run only the transformation step'
    )
    
    parser.add_argument(
        '--load-only',
        action='store_true',
        help='Run only the loading step'
    )
    
    parser.add_argument(
        '--input',
        default='listings.json',
        help='Input file name (default: listings.json)'
    )
    
    parser.add_argument(
        '--mark-stale',
        type=int,
        default=24,
        help='Hours after which to mark listings as stale (default: 24)'
    )
    
    parser.add_argument(
        '--cleanup-days',
        type=int,
        default=30,
        help='Days after which to delete inactive listings (default: 30)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Configuration du logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialisation de l'orchestrateur
    orchestrator = ETLOrchestrator()
    
    # Exécution selon les arguments
    if args.transform_only:
        result = orchestrator.run_transform_only(args.input)
    elif args.load_only:
        result = orchestrator.run_load_only(
            args.input if args.input != 'listings.json' else 'cleaned_listings.json',
            args.mark_stale,
            args.cleanup_days
        )
    else:
        # Full pipeline par défaut
        result = orchestrator.run_full_pipeline(
            args.input,
            args.mark_stale,
            args.cleanup_days
        )
    
    # Affichage du résultat
    print(json.dumps(result, indent=2, default=str))
    
    # Code de sortie
    return 0 if result['status'] == 'success' else 1


if __name__ == "__main__":
    exit(main())
