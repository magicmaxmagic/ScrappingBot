#!/usr/bin/env python3
"""
Générateur de données de test pour alimenter la base de données
Permet de tester le pipeline ETL et l'insertion en base sans dépendre du scraping
"""

import json
import random
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict
import asyncpg
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDataGenerator:
    """Générateur de données immobilières simulées"""
    
    def __init__(self):
        self.montreal_neighborhoods = [
            "Ville-Marie", "Le Plateau-Mont-Royal", "Rosemont–La Petite-Patrie",
            "Villeray–Saint-Michel–Parc-Extension", "Le Sud-Ouest", "Verdun",
            "Ahuntsic-Cartierville", "Mercier–Hochelaga-Maisonneuve", "Saint-Laurent",
            "Outremont", "Lachine", "LaSalle", "Côte-des-Neiges–Notre-Dame-de-Grâce"
        ]
        
        self.property_types = ["Condo", "Apartment", "Townhouse", "House"]
        
        self.streets = [
            "Rue Saint-Denis", "Boulevard Saint-Laurent", "Rue Sainte-Catherine",
            "Avenue du Parc", "Rue Sherbrooke", "Boulevard René-Lévesque",
            "Rue Saint-Jacques", "Avenue des Pins", "Rue Notre-Dame",
            "Boulevard de Maisonneuve"
        ]

    def generate_listing(self, listing_id: int) -> Dict:
        """Génère une annonce immobilière simulée"""
        neighborhood = random.choice(self.montreal_neighborhoods)
        property_type = random.choice(self.property_types)
        street = random.choice(self.streets)
        street_number = random.randint(100, 9999)
        
        # Prix réaliste selon le quartier
        base_price = {
            "Outremont": 650000,
            "Ville-Marie": 550000,
            "Le Plateau-Mont-Royal": 500000,
            "Westmount": 800000,
        }.get(neighborhood, 400000)
        
        price = base_price + random.randint(-100000, 200000)
        
        # Caractéristiques selon le type de propriété
        if property_type == "Condo":
            bedrooms = random.choice([1, 2, 3])
            bathrooms = random.choice([1, 1.5, 2])
            sqft = random.randint(600, 1800)
        else:
            bedrooms = random.choice([2, 3, 4, 5])
            bathrooms = random.choice([1.5, 2, 2.5, 3])
            sqft = random.randint(1000, 3000)

        return {
            "id": f"test_{listing_id}",
            "url": f"https://test.example.com/listing/{listing_id}",
            "address": f"{street_number} {street}, {neighborhood}, QC",
            "neighborhood": neighborhood,
            "price": price,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "sqft": sqft,
            "property_type": property_type,
            "description": f"Beautiful {property_type.lower()} in {neighborhood} with {bedrooms} bedrooms and {bathrooms} bathrooms. Modern amenities and great location.",
            "listing_date": datetime.now(timezone.utc).isoformat(),
            "source": "test_generator",
            "latitude": 45.5017 + random.uniform(-0.1, 0.1),
            "longitude": -73.5673 + random.uniform(-0.1, 0.1),
            "images": [f"https://test.example.com/images/{listing_id}_{i}.jpg" for i in range(random.randint(3, 8))],
            "features": random.sample([
                "Parking", "Balcony", "Elevator", "Gym", "Pool", "Laundry", 
                "Air Conditioning", "Fireplace", "Storage", "Pet Friendly"
            ], k=random.randint(2, 5))
        }

    def generate_batch(self, count: int = 50) -> List[Dict]:
        """Génère un lot d'annonces"""
        return [self.generate_listing(i) for i in range(1, count + 1)]

    def save_to_json(self, listings: List[Dict], filename: str = "test_listings.json"):
        """Sauvegarde les données en JSON pour l'ETL"""
        logs_dir = Path(__file__).parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        file_path = logs_dir / filename
        
        # Format compatible avec le scraper
        data = {
            "success": True,
            "count": len(listings),
            "strategy": "test_data",
            "blocked": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "listings": listings
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Données de test sauvegardées : {file_path}")
        return file_path

    async def insert_directly_to_db(self, listings: List[Dict]):
        """Insert directement en base pour tester la DB"""
        try:
            # Configuration de la DB (utilise les mêmes variables que le docker-compose)
            conn = await asyncpg.connect(
                host="localhost",
                port=5432,
                database="scrappingbot",
                user="scrappingbot_user",
                password="scrappingbot_pass"
            )
            
            logger.info(f"Connexion à la base de données établie")
            
            # Insertion des annonces
            for listing in listings:
                try:
                    # Calculer le hash de l'URL (SHA256 des 64 premiers caractères)
                    import hashlib
                    url_hash = hashlib.sha256(listing["url"].encode()).hexdigest()[:64]
                    
                    # Convertir sqft en sqm
                    area_sqm = listing["sqft"] * 0.092903 if listing["sqft"] else None
                    
                    await conn.execute("""
                        INSERT INTO listings (
                            url_hash, url, title, price, currency,
                            area_sqm, bedrooms, bathrooms, property_type, listing_type,
                            address, coordinates, site_domain, published_date, raw_data
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, 
                                 ST_SetSRID(ST_MakePoint($12, $13), 4326), $14, $15, $16)
                        ON CONFLICT (url_hash) DO UPDATE SET
                            price = EXCLUDED.price,
                            updated_at = CURRENT_TIMESTAMP
                    """, 
                        url_hash,
                        listing["url"],
                        listing["description"][:100],  # titre court
                        listing["price"],
                        "CAD",
                        area_sqm,
                        listing["bedrooms"],
                        listing["bathrooms"],
                        listing["property_type"],
                        "sale",  # type d'annonce
                        listing["address"],
                        listing["longitude"],  # longitude en premier pour ST_MakePoint
                        listing["latitude"],   # latitude en second
                        "test.example.com",
                        datetime.now().date(),
                        json.dumps(listing)
                    )
                except Exception as e:
                    logger.error(f"Erreur insertion annonce {listing['id']}: {e}")
            
            await conn.close()
            logger.info(f"Insertion terminée : {len(listings)} annonces insérées")
            
        except Exception as e:
            logger.error(f"Erreur connexion base de données : {e}")
            raise

async def main():
    """Point d'entrée principal"""
    generator = TestDataGenerator()
    
    # Génère des données de test
    logger.info("Génération de données de test...")
    test_listings = generator.generate_batch(count=25)
    
    # Sauvegarde en JSON pour l'ETL
    json_file = generator.save_to_json(test_listings, "preview_test.json")
    
    # Option : insertion directe en base
    try:
        logger.info("Tentative d'insertion directe en base de données...")
        await generator.insert_directly_to_db(test_listings)
        logger.info("✅ Données de test insérées avec succès !")
    except Exception as e:
        logger.warning(f"Insertion directe échouée : {e}")
        logger.info("💡 Utilisez l'ETL pour traiter le fichier JSON généré")

if __name__ == "__main__":
    asyncio.run(main())
