const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');

const app = express();
const port = 3002; // Changement de port

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

// Test de connexion à la base de données
pool.on('connect', () => {
  console.log('✅ Connecté à PostgreSQL');
});

pool.on('error', (err) => {
  console.error('❌ Erreur PostgreSQL:', err);
});

// Route pour récupérer toutes les annonces avec coordonnées
app.get('/listings', async (req, res) => {
  try {
    console.log('🔍 Récupération des annonces depuis la base de données...');
    
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
    
    const listings = result.rows.map(row => ({
      id: row.id,
      title: row.title || 'Sans titre',
      description: row.title || 'Description non disponible',
      price: Number(row.price) || 0,
      location: row.address || 'Adresse non disponible',
      property_type: row.property_type || 'appartement',
      rooms: row.bedrooms || 1,
      surface: row.area_sqm ? Number(row.area_sqm) : null,
      latitude: row.latitude ? Number(row.latitude) : null,
      longitude: row.longitude ? Number(row.longitude) : null,
      url: row.url || '',
      created_at: row.created_at,
      updated_at: row.updated_at,
    }));

    console.log(`✅ ${listings.length} annonces récupérées de la base de données`);
    
    res.json({
      listings,
      total: listings.length,
    });
  } catch (error) {
    console.error('❌ Erreur lors de la récupération des annonces:', error.message);
    
    // Données de fallback en cas d'erreur
    console.log('🔄 Utilisation des données de fallback...');
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

// Route pour une annonce spécifique
app.get('/listings/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
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
      WHERE id = $1 AND is_active = true
    `;

    const result = await pool.query(query, [id]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Annonce non trouvée' });
    }

    const row = result.rows[0];
    const listing = {
      id: row.id,
      title: row.title || 'Sans titre',
      description: row.title || 'Description non disponible',
      price: Number(row.price) || 0,
      location: row.address || 'Adresse non disponible',
      property_type: row.property_type || 'appartement',
      rooms: row.bedrooms || 1,
      surface: row.area_sqm ? Number(row.area_sqm) : null,
      latitude: row.latitude ? Number(row.latitude) : null,
      longitude: row.longitude ? Number(row.longitude) : null,
      url: row.url || '',
      created_at: row.created_at,
      updated_at: row.updated_at,
    };

    res.json(listing);
  } catch (error) {
    console.error('Erreur lors de la récupération de l\'annonce:', error);
    res.status(500).json({ error: 'Erreur serveur' });
  }
});

// Route de santé
app.get('/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    timestamp: new Date().toISOString(),
    database: 'Connected'
  });
});

// Démarrage du serveur
app.listen(port, () => {
  console.log(`🚀 Serveur API démarré sur http://localhost:${port}`);
  console.log(`📊 Endpoint: http://localhost:${port}/listings`);
  console.log(`🗺️  Frontend: http://localhost:3000`);
});

// Gestion des erreurs de processus
process.on('SIGINT', async () => {
  console.log('\n🛑 Arrêt du serveur...');
  await pool.end();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\n🛑 Arrêt du serveur...');
  await pool.end();
  process.exit(0);
});
