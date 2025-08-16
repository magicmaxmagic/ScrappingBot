"""
Configuration centralisée des logs pour les services Python
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

def create_log_directories():
    """Créer les dossiers de logs s'ils n'existent pas"""
    log_dirs = [
        'logs/api',
        'logs/frontend', 
        'logs/scraper',
        'logs/etl',
        'logs/chatbot',
        'logs/database',
        'logs/system'
    ]
    
    for log_dir in log_dirs:
        Path(log_dir).mkdir(parents=True, exist_ok=True)

def get_log_path(service: str, log_type: str = 'app') -> str:
    """Obtenir le chemin du fichier de log"""
    create_log_directories()
    timestamp = datetime.now().strftime('%Y-%m-%d')
    return f'logs/{service}/{log_type}-{timestamp}.log'

def setup_logger(service: str, level: str = 'INFO'):
    """Configurer un logger pour un service donné"""
    
    # Créer le logger
    logger = logging.getLogger(service)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Éviter la duplication des handlers
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
    )
    
    # Handler pour tous les logs
    all_handler = logging.handlers.RotatingFileHandler(
        get_log_path(service, 'all'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(formatter)
    logger.addHandler(all_handler)
    
    # Handler pour les erreurs uniquement
    error_handler = logging.handlers.RotatingFileHandler(
        get_log_path(service, 'error'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # Handler console en développement
    if os.getenv('ENVIRONMENT', 'development') == 'development':
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger

# Loggers prédéfinis pour chaque service
def get_api_logger():
    return setup_logger('api')

def get_scraper_logger():
    return setup_logger('scraper')

def get_etl_logger():
    return setup_logger('etl')

def get_chatbot_logger():
    return setup_logger('chatbot')

def get_database_logger():
    return setup_logger('database')
