const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');

const app = express();
const port = 3001;

// Configuration de la base de données
const pool = new Pool({
  user: 'scrappingbot_user',
  host: 'localhost',
  database: 'scrappingbot',
  password: 'scrappingbot_pass',
  port: 5432,
});

app.use(cors());
app.use(express.json());

// Route pour récupérer toutes les annonces avec coordonnées
app.get('/listings', async (req, res) => {
  try {
    const query = `
      SELECT 
        id,
        title,
        price,
        property_type,
        address,
        area_sqm,
        bedrooms,
        bathrooms,
        CASE 
          WHEN coordinates IS NOT NULL 
          THEN ST_Y(coordinates) 
          ELSE NULL 
        END as latitude,
        CASE 
          WHEN coordinates IS NOT NULL 
          THEN ST_X(coordinates) 
          ELSE NULL 
        END as longitude,
        url,
        scraped_at as created_at,
        updated_at
      FROM listings 
      WHERE is_active = true
      ORDER BY scraped_at DESC
    `;

    const result = await pool.query(query);
    
    const listings = result.rows.map(listing => ({
      id: listing.id,
      title: listing.title || 'Sans titre',
      description: listing.title || 'Description non disponible',
      price: Number(listing.price) || 0,
      location: listing.address || 'Adresse non disponible',
      property_type: listing.property_type || 'appartement',
      rooms: listing.bedrooms || 1,
      surface: listing.area_sqm ? Number(listing.area_sqm) : null,
      latitude: listing.latitude ? Number(listing.latitude) : null,
      longitude: listing.longitude ? Number(listing.longitude) : null,
      url: listing.url || '',
      created_at: listing.created_at,
      updated_at: listing.updated_at,
    }));

    console.log(`Returning ${listings.length} listings from database`);
    
    res.json({
      listings,
      total: listings.length,
    });
  } catch (error) {
    console.error('Erreur lors de la récupération des annonces:', error);
    
    // Données de fallback en cas d'erreur
    const mockListings = [
      {
        id: '1',
        title: 'Superbe condo 2BR dans Ville-Marie',
        description: 'Magnifique condo avec vue sur le fleuve',
        price: 450000,
        location: '1234 Rue Saint-Denis, Ville-Marie, QC',
        property_type: 'condo',
        rooms: 2,
        surface: 85,
        latitude: 45.5088,
        longitude: -73.5878,
        url: 'https://example.com/listing/1',
        created_at: new Date(),
        updated_at: new Date(),
      },
      {
        id: '2',
        title: 'Appartement 3BR Plateau-Mont-Royal',
        description: 'Charmant appartement dans le Plateau',
        price: 525000,
        location: '5678 Boulevard Saint-Laurent, Le Plateau-Mont-Royal, QC',
        property_type: 'appartement',
        rooms: 3,
        surface: 120,
        latitude: 45.5276,
        longitude: -73.5825,
        url: 'https://example.com/listing/2',
        created_at: new Date(),
        updated_at: new Date(),
      },
      {
        id: '3',
        title: 'Maison 4BR Outremont',
        description: 'Belle maison familiale à Outremont',
        price: 850000,
        location: '9876 Avenue du Parc, Outremont, QC',
        property_type: 'maison',
        rooms: 4,
        surface: 200,
        latitude: 45.5234,
        longitude: -73.6078,
        url: 'https://example.com/listing/3',
        created_at: new Date(),
        updated_at: new Date(),
      },
      {
        id: '4',
        title: 'Loft 1BR Griffintown',
        description: 'Loft moderne dans Griffintown',
        price: 320000,
        location: '1111 Rue Notre-Dame, Le Sud-Ouest, QC',
        property_type: 'loft',
        rooms: 1,
        surface: 60,
        latitude: 45.4942,
        longitude: -73.5597,
        url: 'https://example.com/listing/4',
        created_at: new Date(),
        updated_at: new Date(),
      },
      {
        id: '5',
        title: 'Townhouse 3BR Verdun',
        description: 'Maison de ville à Verdun',
        price: 475000,
        location: '2222 Rue Wellington, Verdun, QC',
        property_type: 'maison',
        rooms: 3,
        surface: 140,
        latitude: 45.4533,
        longitude: -73.5673,
        url: 'https://example.com/listing/5',
        created_at: new Date(),
        updated_at: new Date(),
      },
    ];

    res.json({
      listings: mockListings,
      total: mockListings.length,
    });
  }
});
        bedrooms,
        bathrooms,
        CASE 
          WHEN coordinates IS NOT NULL 
          THEN ST_Y(coordinates) 
          ELSE NULL 
        END as latitude,
        CASE 
          WHEN coordinates IS NOT NULL 
          THEN ST_X(coordinates) 
          ELSE NULL 
        END as longitude,
        url,
        scraped_at as created_at,
        updated_at
      FROM listings 
      WHERE is_active = true
      ORDER BY scraped_at DESC
    ;

    const result = await pool.query(query);
    
    const listings = result.rows.map(row => ({
      id: row.id,
      title: row.title || 'Sans titre',
      price: Number(row.price) || 0,
      property_type: row.property_type || 'apartment',
      address: row.address || 'Adresse non disponible',
      area_sqm: row.area_sqm ? Number(row.area_sqm) : undefined,
      bedrooms: row.bedrooms ? Number(row.bedrooms) : undefined,
      bathrooms: row.bathrooms ? Number(row.bathrooms) : undefined,
      latitude: row.latitude ? Number(row.latitude) : undefined,
      longitude: row.longitude ? Number(row.longitude) : undefined,
      url: row.url || '',
      created_at: row.created_at,
      updated_at: row.updated_at,
    }));

    res.json({
      listings,
      total: listings.length,
    });
  } catch (error) {
    console.error('Erreur lors de la récupération des annonces:', error);
    
    // Fallback avec données mock
    const mockListings = [
      {
        id: '1',
        title: 'Superbe condo 2BR dans Ville-Marie',
        price: 450000,
        property_type: 'Condo',
        address: '1234 Rue Saint-Denis, Ville-Marie, QC',
        area_sqm: 85,
        bedrooms: 2,
        bathrooms: 1,
        latitude: 45.5088,
        longitude: -73.5878,
        url: 'https://example.com/listing/1',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: '2',
        title: 'Appartement 3BR Plateau-Mont-Royal',
        price: 525000,
        property_type: 'Apartment',
        address: '5678 Boulevard Saint-Laurent, Le Plateau-Mont-Royal, QC',
        area_sqm: 120,
        bedrooms: 3,
        bathrooms: 2,
        latitude: 45.5276,
        longitude: -73.5825,
        url: 'https://example.com/listing/2',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: '3',
        title: 'Maison 4BR Outremont',
        price: 850000,
        property_type: 'House',
        address: '9876 Avenue du Parc, Outremont, QC',
        area_sqm: 200,
        bedrooms: 4,
        bathrooms: 3,
        latitude: 45.5234,
        longitude: -73.6078,
        url: 'https://example.com/listing/3',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: '4',
        title: 'Loft 1BR Griffintown',
        price: 320000,
        property_type: 'Condo',
        address: '1111 Rue Notre-Dame, Le Sud-Ouest, QC',
        area_sqm: 60,
        bedrooms: 1,
        bathrooms: 1,
        latitude: 45.4942,
        longitude: -73.5597,
        url: 'https://example.com/listing/4',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: '5',
        title: 'Townhouse 3BR Verdun',
        price: 475000,
        property_type: 'Townhouse',
        address: '2222 Rue Wellington, Verdun, QC',
        area_sqm: 140,
        bedrooms: 3,
        bathrooms: 2,
        latitude: 45.4533,
        longitude: -73.5673,
        url: 'https://example.com/listing/5',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];

    res.json({
      listings: mockListings,
      total: mockListings.length,
    });
  }
});

// Route de santé
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

app.listen(port, () => {
  console.log(`🚀 API Server running at http://localhost:${port}`);
  console.log(`📍 Map available at http://localhost:3000/map`);
  console.log(`📊 Analytics available at http://localhost:3000/analytics`);
});

// Gestion gracieuse de l'arrêt
process.on('SIGTERM', () => {
  console.log('🛑 Arrêt du serveur...');
  pool.end();
});

process.on('SIGINT', () => {
  console.log('🛑 Arrêt du serveur...');
  pool.end();
  process.exit(0);
});
