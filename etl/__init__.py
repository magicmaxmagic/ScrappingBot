"""
ETL Pipeline pour ScrappingBot
==============================

Pipeline complet Extract-Transform-Load pour traiter les données
de scraping immobilier et les charger dans PostgreSQL+PostGIS.
"""

from typing import Dict, List, Any, Optional, Tuple, Callable, Union, cast
import logging
import json
from pathlib import Path
from datetime import datetime
import re
import hashlib

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataExtractor:
    """Extraction des données depuis différentes sources."""
    
    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = data_dir
        
    def extract_from_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Extrait les données d'un fichier JSON."""
        try:
            with open(self.data_dir / file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Extracted {len(data)} records from {file_path}")
                return data if isinstance(data, list) else [data]
        except FileNotFoundError:
            logger.warning(f"File {file_path} not found")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {file_path}: {e}")
            return []
    
    def extract_from_scraper_output(self) -> List[Dict[str, Any]]:
        """Extrait les données du scraper."""
        return self.extract_from_json("listings.json")
    
    def extract_from_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extrait/valide des données déjà chargées en mémoire."""
        if not isinstance(data, list):
            return []
        return data


class DataTransformer:
    """Transformation et nettoyage des données."""
    
    def __init__(self):
        self.required_fields = ['title', 'price', 'url']

        # helper to convert "500k" -> "500000"
        def _k_to_num(m: re.Match) -> str:
            return str(int(m.group(1)) * 1000)

        # patterns can be either a replacement string or a callable that accepts a re.Match and returns a str
        self.price_patterns: Dict[str, Union[str, Callable[[re.Match], str]]] = {
            r'(\d+(?:\s?\d+)*)\s*\$': r'\1',  # 500 000 $ -> 500000
            r'\$\s*(\d+(?:,\d+)*)': r'\1',     # $500,000 -> 500000
            r'(\d+)k': _k_to_num  # 500k -> 500000
        }
    
    def clean_price(self, price_str: Optional[Any]) -> Optional[float]:
        """Nettoie et normalise les prix."""
        if price_str is None:
            return None

        cleaned = str(price_str).strip()
        if not cleaned:
            return None
        
        # Appliquer les patterns de nettoyage
        for pattern, replacement in self.price_patterns.items():
            if callable(replacement):
                cleaned = re.sub(pattern, replacement, cleaned)
            else:
                cleaned = re.sub(pattern, replacement, cleaned)
        
        # Extraire le nombre
        numbers = re.findall(r'\d+', cleaned.replace(',', '').replace(' ', ''))
        if numbers:
            try:
                return float(''.join(numbers))
            except ValueError:
                pass
        
        return None
    
    def clean_area(self, area_str: Optional[Any], unit: Optional[str] = None) -> Optional[float]:
        """Nettoie et convertit les surfaces en m²."""
        if not area_str:
            return None
            
        # Extraire les chiffres
        numbers = re.findall(r'\d+(?:\.\d+)?', str(area_str).replace(',', '.'))
        if not numbers:
            return None
            
        area = float(numbers[0])
        
        # Conversion selon l'unité
        if unit and 'ft' in unit.lower():
            area = area * 0.092903  # ft² vers m²
        elif unit and 'sq' in unit.lower() and 'ft' in unit.lower():
            area = area * 0.092903
            
        return round(area, 2)
    
    def extract_coordinates(self, text: str) -> Tuple[Optional[float], Optional[float]]:
        """Extrait les coordonnées GPS du texte."""
        # Pattern pour latitude/longitude
        coord_pattern = r'(-?\d+\.?\d*),?\s*(-?\d+\.?\d*)'
        matches = re.findall(coord_pattern, text)
        
        for lat_str, lon_str in matches:
            try:
                lat, lon = float(lat_str), float(lon_str)
                # Vérifier que les coordonnées sont valides (approximativement Montréal)
                if 45.0 <= lat <= 46.0 and -74.5 <= lon <= -73.0:
                    return lat, lon
            except ValueError:
                continue
                
        return None, None
    
    def generate_listing_hash(self, listing: Dict[str, Any]) -> str:
        """Génère un hash unique pour identifier les doublons."""
        key_fields = [
            str(listing.get('title', '')),
            str(listing.get('price', '')),
            str(listing.get('address', '')),
            str(listing.get('url', ''))
        ]
        combined = '|'.join(key_fields).lower()
        return hashlib.md5(combined.encode()).hexdigest()
    
    def transform_listing(self, raw_listing: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transforme une annonce brute en format standardisé."""
        # Vérifier les champs obligatoires
        for field in self.required_fields:
            if not raw_listing.get(field):
                logger.warning(f"Missing required field '{field}' in listing")
                return None
        
        # Transformation des données
        transformed = {
            'id': raw_listing.get('id'),
            'title': str(raw_listing.get('title', '')).strip(),
            'description': str(raw_listing.get('description', '')).strip(),
            'price': self.clean_price(raw_listing.get('price')),
            'area': self.clean_area(raw_listing.get('area'), raw_listing.get('area_unit')),
            'bedrooms': self._safe_int(raw_listing.get('bedrooms')),
            'bathrooms': self._safe_float(raw_listing.get('bathrooms')),
            'address': str(raw_listing.get('address', '')).strip(),
            'neighborhood': str(raw_listing.get('neighborhood', '')).strip(),
            'city': str(raw_listing.get('city', 'Montreal')).strip(),
            'province': str(raw_listing.get('province', 'QC')).strip(),
            'postal_code': self._clean_postal_code(raw_listing.get('postal_code')),
            'property_type': str(raw_listing.get('property_type', '')).strip(),
            'listing_type': str(raw_listing.get('listing_type', 'sale')).strip(),
            'url': str(raw_listing.get('url', '')).strip(),
            'source': str(raw_listing.get('source', 'scraper')).strip(),
            'scraped_at': raw_listing.get('scraped_at', datetime.now().isoformat()),
            'images': raw_listing.get('images', []),
            'features': raw_listing.get('features', [])
        }
        
        # Extraction des coordonnées
        if raw_listing.get('location'):
            transformed['latitude'], transformed['longitude'] = self.extract_coordinates(
                str(raw_listing.get('location'))
            )
        else:
            transformed['latitude'] = self._safe_float(raw_listing.get('latitude'))
            transformed['longitude'] = self._safe_float(raw_listing.get('longitude'))
        
        # Génération du hash pour la déduplication
        transformed['hash'] = self.generate_listing_hash(transformed)
        
        return transformed
    
    def _safe_int(self, value) -> Optional[int]:
        """Conversion sécurisée vers entier."""
        if value is None:
            return None
        try:
            return int(float(str(value).replace(',', '.')))
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, value) -> Optional[float]:
        """Conversion sécurisée vers float."""
        if value is None:
            return None
        try:
            return float(str(value).replace(',', '.'))
        except (ValueError, TypeError):
            return None
    
    def _clean_postal_code(self, postal_code: Optional[Any]) -> Optional[str]:
        """Nettoie le code postal canadien."""
        if not postal_code:
            return None
        
        # Pattern pour code postal canadien
        cleaned = re.sub(r'[^A-Za-z0-9]', '', str(postal_code).upper())
        if len(cleaned) == 6 and re.match(r'[A-Z]\d[A-Z]\d[A-Z]\d', cleaned):
            return f"{cleaned[:3]} {cleaned[3:]}"
        
        return None
    
    def deduplicate(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Supprime les doublons basés sur le hash."""
        seen_hashes = set()
        unique_listings = []
        
        for listing in listings:
            listing_hash = listing.get('hash')
            if listing_hash not in seen_hashes:
                seen_hashes.add(listing_hash)
                unique_listings.append(listing)
            else:
                logger.debug(f"Duplicate found: {listing.get('title', 'No title')}")
        
        logger.info(f"Deduplication: {len(listings)} -> {len(unique_listings)} listings")
        return unique_listings
    
    def transform(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transforme une liste d'annonces."""
        transformed = []
        for listing in listings:
            transformed_listing = self.transform_listing(listing)
            if transformed_listing:
                transformed.append(transformed_listing)
        
        # Déduplication
        return self.deduplicate(transformed)


class DataValidator:
    """Validation des données transformées."""
    
    def validate_listing(self, listing: Dict[str, Any]) -> bool:
        """Valide une annonce transformée."""
        errors = []
        
        # Validation des champs obligatoires
        required_fields = ['title', 'price', 'url', 'hash']
        for field in required_fields:
            if not listing.get(field):
                errors.append(f"Missing {field}")
        
        # Validation des types de données
        if listing.get('price') is not None and (not isinstance(listing['price'], (int, float)) or listing['price'] <= 0):
            errors.append("Invalid price")
        
        if listing.get('area') is not None and (not isinstance(listing['area'], (int, float)) or listing['area'] <= 0):
            errors.append("Invalid area")
        
        # Validation des coordonnées
        lat, lon = listing.get('latitude'), listing.get('longitude')
        if lat is not None and lon is not None:
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                errors.append("Invalid coordinates")
        
        if errors:
            logger.warning(f"Validation errors for {listing.get('url', 'unknown')}: {', '.join(errors)}")
            return False
        
        return True
    
    def validate_batch(self, listings: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Valide un lot d'annonces."""
        valid_listings = []
        invalid_listings = []
        
        for listing in listings:
            if self.validate_listing(listing):
                valid_listings.append(listing)
            else:
                invalid_listings.append(listing)
        
        logger.info(f"Validation: {len(valid_listings)} valid, {len(invalid_listings)} invalid")
        return valid_listings, invalid_listings
    
    def validate(self, listings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Valide une liste d'annonces et retourne les statistiques."""
        valid_listings, invalid_listings = self.validate_batch(listings)
        return {
            "valid_count": len(valid_listings),
            "invalid_count": len(invalid_listings),
            "valid_listings": valid_listings,
            "invalid_listings": invalid_listings
        }


def run_etl_pipeline(input_file: str = "listings.json", output_file: str = "cleaned_listings.json") -> Dict[str, Any]:
    """
    Exécute le pipeline ETL complet.
    
    Returns:
        Rapport d'exécution avec statistiques
    """
    start_time = datetime.now()
    logger.info("Starting ETL pipeline")
    
    # Initialisation des composants
    extractor = DataExtractor()
    transformer = DataTransformer()
    validator = DataValidator()
    
    # Extract
    raw_listings = extractor.extract_from_scraper_output()
    
    if not raw_listings:
        logger.warning("No data to process")
        return {
            'status': 'success',
            'stats': {
                'extracted': 0,
                'transformed': 0,
                'deduplicated': 0,
                'valid': 0,
                'invalid': 0,
                'loaded': 0
            },
            'execution_time': (datetime.now() - start_time).total_seconds()
        }
    
    # Transform
    transformed_listings = []
    for raw_listing in raw_listings:
        transformed = transformer.transform_listing(raw_listing)
        if transformed:
            transformed_listings.append(transformed)
    
    # Deduplicate
    deduplicated_listings = transformer.deduplicate(transformed_listings)
    
    # Validate
    valid_listings, invalid_listings = validator.validate_batch(deduplicated_listings)
    
    # Save results
    output_path = Path("data") / output_file
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(valid_listings, f, indent=2, ensure_ascii=False, default=str)
    
    # Generate report
    stats = {
        'extracted': len(raw_listings),
        'transformed': len(transformed_listings),
        'deduplicated': len(deduplicated_listings),
        'valid': len(valid_listings),
        'invalid': len(invalid_listings),
        'loaded': len(valid_listings)
    }
    
    execution_time = (datetime.now() - start_time).total_seconds()
    
    report = {
        'status': 'success',
        'stats': stats,
        'execution_time': execution_time,
        'timestamp': datetime.now().isoformat()
    }
    
    # Save report
    with open(Path("data") / "etl_report.json", 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"ETL pipeline completed in {execution_time:.2f}s")
    logger.info(f"Stats: {stats}")
    
    return report


if __name__ == "__main__":
    run_etl_pipeline()
