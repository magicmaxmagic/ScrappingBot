-- Script SQL pour insérer des données de test directement dans la base
-- Compatible avec le schéma existant

BEGIN;

-- Supprimer les données de test existantes (au cas où)
DELETE FROM listings WHERE site_domain = 'test.example.com';

-- Insérer des données de test dans la table listings
INSERT INTO listings (
    url_hash, url, title, price, currency,
    area_sqm, bedrooms, bathrooms, property_type, listing_type,
    address, coordinates, site_domain, published_date, raw_data
) VALUES
(
    md5('https://test.example.com/listing/1'),
    'https://test.example.com/listing/1',
    'Superbe condo 2BR dans Ville-Marie',
    450000,
    'CAD',
    85.5,
    2,
    1.5,
    'Condo',
    'sale',
    '1234 Rue Saint-Denis, Ville-Marie, QC',
    ST_SetSRID(ST_MakePoint(-73.5673, 45.5017), 4326),
    'test.example.com',
    CURRENT_DATE,
    '{"bedrooms": 2, "bathrooms": 1.5, "features": ["Parking", "Balcony"], "source": "test"}'::jsonb
),
(
    md5('https://test.example.com/listing/2'),
    'https://test.example.com/listing/2',
    'Appartement 3BR Plateau-Mont-Royal',
    525000,
    'CAD',
    112.3,
    3,
    2,
    'Apartment',
    'sale',
    '5678 Boulevard Saint-Laurent, Le Plateau-Mont-Royal, QC',
    ST_SetSRID(ST_MakePoint(-73.5850, 45.5200), 4326),
    'test.example.com',
    CURRENT_DATE,
    '{"bedrooms": 3, "bathrooms": 2, "features": ["Elevator", "Gym"], "source": "test"}'::jsonb
),
(
    md5('https://test.example.com/listing/3'),
    'https://test.example.com/listing/3',
    'Maison 4BR Outremont',
    850000,
    'CAD',
    185.2,
    4,
    3,
    'House',
    'sale',
    '9876 Avenue du Parc, Outremont, QC',
    ST_SetSRID(ST_MakePoint(-73.6103, 45.5125), 4326),
    'test.example.com',
    CURRENT_DATE,
    '{"bedrooms": 4, "bathrooms": 3, "features": ["Parking", "Fireplace", "Pool"], "source": "test"}'::jsonb
),
(
    md5('https://test.example.com/listing/4'),
    'https://test.example.com/listing/4',
    'Loft 1BR Griffintown',
    320000,
    'CAD',
    65.8,
    1,
    1,
    'Condo',
    'sale',
    '1111 Rue Notre-Dame, Le Sud-Ouest, QC',
    ST_SetSRID(ST_MakePoint(-73.5540, 45.4950), 4326),
    'test.example.com',
    CURRENT_DATE,
    '{"bedrooms": 1, "bathrooms": 1, "features": ["Gym", "Pool"], "source": "test"}'::jsonb
),
(
    md5('https://test.example.com/listing/5'),
    'https://test.example.com/listing/5',
    'Townhouse 3BR Verdun',
    475000,
    'CAD',
    134.7,
    3,
    2.5,
    'Townhouse',
    'sale',
    '2222 Rue Wellington, Verdun, QC',
    ST_SetSRID(ST_MakePoint(-73.5684, 45.4584), 4326),
    'test.example.com',
    CURRENT_DATE,
    '{"bedrooms": 3, "bathrooms": 2.5, "features": ["Parking", "Storage"], "source": "test"}'::jsonb
);

-- Insérer quelques logs de scraping pour simuler l'activité
INSERT INTO scrape_logs (
    source, url, status, listings_found, 
    scraped_at, strategy_used
) VALUES
(
    'test_generator',
    'https://test.example.com',
    'success',
    5,
    NOW(),
    'test_data'
);

COMMIT;

-- Afficher un résumé des données insérées
SELECT 
    COUNT(*) as total_listings,
    AVG(price) as avg_price,
    COUNT(DISTINCT property_type) as property_types
FROM listings 
WHERE site_domain = 'test.example.com';

SELECT 'Données de test insérées avec succès!' as status;
