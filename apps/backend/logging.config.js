/**
 * Configuration centralisée des logs pour ScrappingBot
 * Tous les services doivent utiliser cette configuration
 */

const path = require('path');
const fs = require('fs');

// Créer les dossiers de logs s'ils n'existent pas
const createLogDirectories = () => {
  const projectRoot = path.join(__dirname, '..', '..');
  const logDirs = [
    'logs/api',
    'logs/frontend', 
    'logs/scraper',
    'logs/etl',
    'logs/chatbot',
    'logs/database',
    'logs/system'
  ];

  logDirs.forEach(dir => {
    const fullPath = path.join(projectRoot, dir);
    if (!fs.existsSync(fullPath)) {
      fs.mkdirSync(fullPath, { recursive: true });
    }
  });
};

// Fonction pour obtenir le chemin du fichier de log
const getLogPath = (service, type = 'app') => {
  createLogDirectories();
  const timestamp = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
  // Utiliser le dossier racine du projet
  const projectRoot = path.join(__dirname, '..', '..');
  return path.join(projectRoot, 'logs', service, `${type}-${timestamp}.log`);
};

// Configuration pour Winston (Node.js)
const createWinstonConfig = (service) => {
  const winston = require('winston');
  
  return winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
      winston.format.timestamp(),
      winston.format.errors({ stack: true }),
      winston.format.json()
    ),
    defaultMeta: { service },
    transports: [
      // Fichier pour tous les logs
      new winston.transports.File({
        filename: getLogPath(service, 'all'),
        level: 'debug'
      }),
      // Fichier pour les erreurs uniquement
      new winston.transports.File({
        filename: getLogPath(service, 'error'),
        level: 'error'
      }),
      // Console en mode développement
      ...(process.env.NODE_ENV !== 'production' ? [
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          )
        })
      ] : [])
    ]
  });
};

// Configuration pour les logs Python
const getPythonLogConfig = (service) => ({
  version: 1,
  disable_existing_loggers: false,
  formatters: {
    standard: {
      format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    },
    detailed: {
      format: '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
    }
  },
  handlers: {
    console: {
      level: 'INFO',
      class: 'logging.StreamHandler',
      formatter: 'standard'
    },
    file_all: {
      level: 'DEBUG',
      class: 'logging.handlers.RotatingFileHandler',
      filename: getLogPath(service, 'all'),
      maxBytes: 10485760, // 10MB
      backupCount: 5,
      formatter: 'detailed'
    },
    file_error: {
      level: 'ERROR',
      class: 'logging.handlers.RotatingFileHandler',
      filename: getLogPath(service, 'error'),
      maxBytes: 10485760, // 10MB
      backupCount: 5,
      formatter: 'detailed'
    }
  },
  loggers: {
    '': {
      handlers: ['console', 'file_all', 'file_error'],
      level: 'DEBUG',
      propagate: false
    }
  }
});

module.exports = {
  createLogDirectories,
  getLogPath,
  createWinstonConfig,
  getPythonLogConfig
};
