#!/usr/bin/env python3
"""
Script pour déclencher le pipeline ETL avec des données de test
Permet de tester l'ensemble du flux : scraping -> ETL -> base de données
"""

import asyncio
import requests
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

async def trigger_etl_pipeline():
    """Déclenche le pipeline ETL via l'API"""
    
    # 1. Générer des données de test
    logger.info("🔄 Génération de données de test...")
    
    # Importer et exécuter le générateur
    import sys
    sys.path.append(str(Path(__file__).parent))
    
    from test_data_generator import TestDataGenerator
    
    generator = TestDataGenerator()
    test_listings = generator.generate_batch(count=20)
    
    # Sauvegarder dans le format attendu par l'ETL
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    test_file = logs_dir / "preview_realtor.json"
    
    data = {
        "success": True,
        "count": len(test_listings),
        "strategy": "test_data",
        "blocked": False,
        "timestamp": "2025-08-15T19:30:00Z",
        "listings": test_listings
    }
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Données de test créées : {test_file}")
    
    # 2. Déclencher l'ETL via l'API
    logger.info("🚀 Déclenchement du pipeline ETL...")
    
    try:
        # Appel à l'API ETL pour traiter les données
        response = requests.post(
            "http://localhost:8788/etl/full",
            json={
                "input_file": "preview_realtor.json"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ ETL traitement réussi : {result}")
            return result
        else:
            logger.error(f"❌ Erreur ETL : {response.status_code} - {response.text}")
            return None
                    
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'appel ETL : {e}")
        return None

async def check_database_content():
    """Vérifie le contenu de la base de données après ETL"""
    try:
        import asyncpg
        
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            database="scrappingbot",
            user="scrappingbot_user",
            password="scrappingbot_pass"
        )
        
        # Compter les enregistrements
        listings_count = await conn.fetchval("SELECT COUNT(*) FROM listings")
        areas_count = await conn.fetchval("SELECT COUNT(*) FROM areas")
        metrics_count = await conn.fetchval("SELECT COUNT(*) FROM area_metrics")
        logs_count = await conn.fetchval("SELECT COUNT(*) FROM scrape_logs")
        
        logger.info(f"📊 Contenu de la base de données :")
        logger.info(f"  - Listings : {listings_count}")
        logger.info(f"  - Areas : {areas_count}")  
        logger.info(f"  - Area metrics : {metrics_count}")
        logger.info(f"  - Scrape logs : {logs_count}")
        
        # Afficher quelques exemples
        if listings_count > 0:
            sample_listings = await conn.fetch(
                "SELECT address, price, bedrooms, bathrooms FROM listings LIMIT 3"
            )
            logger.info("📋 Exemples d'annonces :")
            for listing in sample_listings:
                logger.info(f"  - {listing['address']} - ${listing['price']:,} - {listing['bedrooms']}BR/{listing['bathrooms']}BA")
        
        await conn.close()
        return {
            "listings": listings_count,
            "areas": areas_count,
            "metrics": metrics_count,
            "logs": logs_count
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur vérification base : {e}")
        return None

async def main():
    """Point d'entrée principal"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    logger.info("🚀 Démarrage du test du pipeline ETL")
    
    # 1. Déclencher ETL avec données de test
    etl_result = await trigger_etl_pipeline()
    
    if etl_result:
        logger.info("✅ Pipeline ETL exécuté avec succès")
        
        # 2. Vérifier le contenu de la base
        logger.info("🔍 Vérification du contenu de la base de données...")
        await asyncio.sleep(2)  # Laisser le temps à l'ETL de finir
        
        db_content = await check_database_content()
        
        if db_content and db_content["listings"] > 0:
            logger.info("🎉 Succès ! Les données sont maintenant en base de données")
        else:
            logger.warning("⚠️  Aucune donnée trouvée en base - vérifiez les logs ETL")
    else:
        logger.error("❌ Échec du pipeline ETL")

if __name__ == "__main__":
    asyncio.run(main())
