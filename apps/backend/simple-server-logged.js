const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const { createWinstonConfig } = require('./logging.config');

// Configuration du logger
const logger = createWinstonConfig('api');

const app = express();
const PORT = process.env.PORT || 3002;

// Configuration CORS
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:3001'],
  credentials: true
}));

app.use(express.json());

// Configuration PostgreSQL
const pool = new Pool({
  host: process.env.DATABASE_HOST || 'localhost',
  port: process.env.DATABASE_PORT || 5432,
  user: process.env.DATABASE_USERNAME || 'postgres',
  password: process.env.DATABASE_PASSWORD || 'password123',
  database: process.env.DATABASE_NAME || 'scrapping_bot'
});

// Middleware de logging des requêtes
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path}`, {
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    timestamp: new Date().toISOString()
  });
  next();
});

// Données de fallback
const fallbackListings = [
  {
    id: '1',
    title: 'Appartement moderne - Centre-ville Montreal',
    price: 450000,
    property_type: 'Appartement',
    location: 'Montreal, QC',
    latitude: 45.5017,
    longitude: -73.5673,
    bedrooms: 2,
    bathrooms: 2,
    area: 85,
    description: 'Magnifique appartement au cœur de Montreal'
  },
  {
    id: '2', 
    title: 'Maison familiale - Plateau Mont-Royal',
    price: 780000,
    property_type: 'Maison',
    location: 'Plateau Mont-Royal, Montreal, QC',
    latitude: 45.5276,
    longitude: -73.5762,
    bedrooms: 3,
    bathrooms: 2,
    area: 120,
    description: 'Belle maison dans le quartier branché du Plateau'
  },
  {
    id: '3',
    title: 'Condo luxueux - Westmount',
    price: 650000,
    property_type: 'Condo',
    location: 'Westmount, QC',
    latitude: 45.4833,
    longitude: -73.5991,
    bedrooms: 2,
    bathrooms: 2,
    area: 95,
    description: 'Condo haut de gamme avec vue imprenable'
  },
  {
    id: '4',
    title: 'Duplex rénové - Rosemont',
    price: 580000,
    property_type: 'Duplex',
    location: 'Rosemont, Montreal, QC',
    latitude: 45.5394,
    longitude: -73.5789,
    bedrooms: 3,
    bathrooms: 2,
    area: 110,
    description: 'Duplex entièrement rénové dans Rosemont'
  },
  {
    id: '5',
    title: 'Loft industriel - Griffintown',
    price: 520000,
    property_type: 'Loft',
    location: 'Griffintown, Montreal, QC',
    latitude: 45.4925,
    longitude: -73.5583,
    bedrooms: 1,
    bathrooms: 1,
    area: 75,
    description: 'Loft moderne dans le nouveau quartier Griffintown'
  }
];

// Route de santé
app.get('/health', (req, res) => {
  logger.info('Health check requested');
  res.json({ 
    status: 'OK', 
    timestamp: new Date().toISOString(),
    service: 'ScrappingBot API'
  });
});

// Route principale pour les annonces
app.get('/listings', async (req, res) => {
  try {
    logger.info('Récupération des annonces depuis la base de données...');
    
    // Test de connexion à la base de données
    const client = await pool.connect();
    logger.info('✅ Connecté à PostgreSQL');
    
    try {
      // Vérifier si la table existe et a des données
      const result = await client.query(`
        SELECT 
          id,
          title,
          price,
          property_type,
          location,
          ST_X(coordinates::geometry) as longitude,
          ST_Y(coordinates::geometry) as latitude,
          bedrooms,
          bathrooms,
          area,
          description,
          created_at
        FROM listings 
        WHERE status = 'active' 
        ORDER BY created_at DESC 
        LIMIT 50
      `);
      
      if (result.rows && result.rows.length > 0) {
        logger.info(`✅ ${result.rows.length} annonces récupérées de la base de données`);
        
        // Transformer les données pour s'assurer qu'elles ont le bon format
        const listings = result.rows.map(row => ({
          id: row.id,
          title: row.title,
          price: parseInt(row.price) || 0,
          property_type: row.property_type,
          location: row.location,
          latitude: parseFloat(row.latitude) || 0,
          longitude: parseFloat(row.longitude) || 0,
          bedrooms: parseInt(row.bedrooms) || 0,
          bathrooms: parseInt(row.bathrooms) || 0,
          area: parseInt(row.area) || 0,
          description: row.description || '',
          created_at: row.created_at
        }));
        
        res.json({
          success: true,
          count: listings.length,
          data: listings,
          source: 'database'
        });
        
      } else {
        logger.warn('Aucune donnée trouvée dans la base de données, utilisation des données de fallback');
        res.json({
          success: true,
          count: fallbackListings.length,
          data: fallbackListings,
          source: 'fallback'
        });
      }
      
    } catch (queryError) {
      logger.error('❌ Erreur lors de la récupération des annonces:', {
        error: queryError.message,
        stack: queryError.stack
      });
      
      logger.info('🔄 Utilisation des données de fallback...');
      res.json({
        success: true,
        count: fallbackListings.length,
        data: fallbackListings,
        source: 'fallback',
        note: 'Données de démonstration - Erreur de base de données'
      });
      
    } finally {
      client.release();
    }
    
  } catch (connectionError) {
    logger.error('❌ Erreur de connexion à PostgreSQL:', {
      error: connectionError.message,
      stack: connectionError.stack
    });
    
    logger.info('🔄 Utilisation des données de fallback...');
    res.json({
      success: true,
      count: fallbackListings.length,
      data: fallbackListings,
      source: 'fallback',
      note: 'Données de démonstration - Pas de connexion DB'
    });
  }
});

// Route pour une annonce spécifique
app.get('/listings/:id', async (req, res) => {
  const { id } = req.params;
  logger.info(`Récupération de l'annonce ${id}`);
  
  try {
    const client = await pool.connect();
    
    try {
      const result = await client.query(`
        SELECT 
          id,
          title,
          price,
          property_type,
          location,
          ST_X(coordinates::geometry) as longitude,
          ST_Y(coordinates::geometry) as latitude,
          bedrooms,
          bathrooms,
          area,
          description,
          created_at
        FROM listings 
        WHERE id = $1 AND status = 'active'
      `, [id]);
      
      if (result.rows && result.rows.length > 0) {
        const listing = result.rows[0];
        logger.info(`✅ Annonce ${id} trouvée`);
        res.json({
          success: true,
          data: listing,
          source: 'database'
        });
      } else {
        // Chercher dans les données de fallback
        const fallbackListing = fallbackListings.find(l => l.id === id);
        if (fallbackListing) {
          logger.info(`✅ Annonce ${id} trouvée dans les données de fallback`);
          res.json({
            success: true,
            data: fallbackListing,
            source: 'fallback'
          });
        } else {
          logger.warn(`❌ Annonce ${id} non trouvée`);
          res.status(404).json({
            success: false,
            message: 'Annonce non trouvée'
          });
        }
      }
      
    } finally {
      client.release();
    }
    
  } catch (error) {
    logger.error(`❌ Erreur lors de la récupération de l'annonce ${id}:`, {
      error: error.message,
      stack: error.stack
    });
    
    // Essayer les données de fallback
    const fallbackListing = fallbackListings.find(l => l.id === id);
    if (fallbackListing) {
      res.json({
        success: true,
        data: fallbackListing,
        source: 'fallback'
      });
    } else {
      res.status(500).json({
        success: false,
        message: 'Erreur serveur'
      });
    }
  }
});

// Gestionnaire d'erreurs
app.use((error, req, res, next) => {
  logger.error('Erreur non gérée:', {
    error: error.message,
    stack: error.stack,
    url: req.url,
    method: req.method
  });
  
  res.status(500).json({
    success: false,
    message: 'Erreur interne du serveur'
  });
});

// Démarrage du serveur
app.listen(PORT, () => {
  logger.info(`🚀 Serveur API démarré sur http://localhost:${PORT}`);
  logger.info(`📊 Endpoint: http://localhost:${PORT}/listings`);
  logger.info(`🗺️  Frontend: http://localhost:3000`);
  logger.info(`📝 Logs API: logs/api/`);
});

// Gestion gracieuse de l'arrêt
process.on('SIGTERM', () => {
  logger.info('Arrêt gracieux du serveur API...');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('Arrêt du serveur API (Ctrl+C)...');
  process.exit(0);
});
