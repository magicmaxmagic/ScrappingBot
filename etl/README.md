# ETL Pipeline Documentation

## 🔄 Vue d'ensemble

Le pipeline ETL (Extract, Transform, Load) est la couche intermédiaire entre le scraper et la base de données PostgreSQL. Il assure le traitement, la validation et le chargement des données immobilières scrapées.

## 📋 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│     SCRAPER     │───▶│   ETL PIPELINE  │───▶│   POSTGRESQL    │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │                 │
                       │   ETL API       │
                       │   (FastAPI)     │
                       │                 │
                       └─────────────────┘
```

### Composants principaux

1. **DataExtractor** - Extraction des données depuis les fichiers JSON
2. **DataTransformer** - Transformation et nettoyage des données
3. **DataValidator** - Validation et contrôle qualité
4. **PostgreSQLLoader** - Chargement vers PostgreSQL avec support spatial
5. **ETLOrchestrator** - Orchestration du pipeline complet
6. **ScraperETLAdapter** - Interface avec le scraper
7. **ETL API** - Service web pour déclencher et monitorer l'ETL

## 🚀 Utilisation

### Commandes Make disponibles

```bash
# Pipeline complet (Extract + Transform + Load)
make etl-full

# Seulement transformation
make etl-transform

# Seulement chargement
make etl-load

# Scraper + ETL combiné
make scrape-and-etl

# API ETL
make etl-api

# Validation du pipeline
make etl-validate

# Status et rapports
make etl-status
```

### Utilisation directe

```bash
# Pipeline complet
docker-compose run --rm etl python etl/orchestrator.py --full

# Pipeline partiel
docker-compose run --rm etl python etl/orchestrator.py --transform-only
docker-compose run --rm etl python etl/orchestrator.py --load-only

# Avec scraper intégré
docker-compose run --rm etl python etl/scraper_adapter.py --where Montreal --what condo

# Validation
docker-compose run --rm etl python etl/validate.py
```

## 📊 Fonctionnalités

### Extraction
- Lecture des données JSON du scraper
- Support multi-fichiers
- Gestion des erreurs de format

### Transformation
- **Nettoyage des prix** : Conversion "$450,000" → 450000
- **Normalisation des surfaces** : "900 sq ft" → 900
- **Extraction coordonnées** : Géocodage des adresses
- **Déduplication** : Hash-based sur titre + localisation
- **Validation des types** : Contrôle de cohérence

### Chargement
- **PostgreSQL + PostGIS** : Support des données spatiales
- **Upsert intelligent** : Mise à jour ou insertion
- **Indexation automatique** : Index sur localisation et prix
- **Triggers** : Mise à jour automatique des timestamps
- **Transactions** : Rollback en cas d'erreur

### API Web
- **Endpoints RESTful** : Déclenchement à distance
- **Jobs en arrière-plan** : Exécution asynchrone
- **Monitoring** : Status et progression
- **Rapports JSON** : Statistiques détaillées

## 📁 Structure des fichiers

```
etl/
├── __init__.py          # Pipeline principal (Extract, Transform, Load)
├── loader.py            # Chargeur PostgreSQL + PostGIS
├── orchestrator.py      # Orchestrateur avec CLI
├── scraper_adapter.py   # Interface scraper
├── api.py              # Service web FastAPI
├── utils.py            # Utilitaires et logging
├── validate.py         # Script de validation
└── README.md           # Cette documentation
```

## 🔧 Configuration

### Variables d'environnement

```bash
# Base de données
POSTGRES_HOST=postgres
POSTGRES_DB=real_estate
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# ETL
ETL_BATCH_SIZE=100
ETL_LOG_LEVEL=INFO
ETL_DATA_PATH=/app/data
```

### Fichiers de configuration

- **docker-compose.yml** : Service ETL configuré
- **Dockerfile.etl** : Container ETL avec dépendances
- **.env** : Variables d'environnement

## 📈 Monitoring et Rapports

### Rapports générés

1. **etl_report.json** - Rapport phase individuelle
2. **etl_full_report.json** - Rapport pipeline complet
3. **etl_validation_report.json** - Rapport de validation

### Structure des rapports

```json
{
  "phase": "full_pipeline",
  "timestamp": "2024-01-15T10:30:00",
  "duration_seconds": 45.2,
  "success": true,
  "stats": {
    "extracted_records": 150,
    "transformed_records": 148,
    "loaded_records": 148,
    "deduplicated": 2,
    "quality_score": 95.3
  },
  "errors": []
}
```

## 🧪 Tests et Validation

### Validation complète
```bash
make etl-validate
```

### Tests individuels
```bash
# Test extraction
docker-compose run --rm etl python etl/validate.py --component extraction

# Test qualité données
docker-compose run --rm etl python etl/validate.py --component quality

# Test connexion DB
docker-compose run --rm etl python etl/validate.py --component database

# Test composants ETL
docker-compose run --rm etl python etl/validate.py --component etl
```

## 🐛 Dépannage

### Problèmes courants

1. **Erreur de connexion DB**
   ```bash
   # Vérifier que PostgreSQL est démarré
   make db-status
   
   # Redémarrer si nécessaire
   make db-restart
   ```

2. **Données manquantes**
   ```bash
   # Vérifier les données source
   ls -la data/scraped_data.json
   
   # Lancer le scraper
   make scrape-test
   ```

3. **Erreurs de transformation**
   ```bash
   # Voir les logs
   docker-compose logs etl
   
   # Validation des données
   make etl-validate
   ```

### Logs

```bash
# Logs du service ETL
docker-compose logs -f etl

# Logs dans le container
docker-compose exec etl tail -f /app/logs/etl.log
```

## 🔒 Sécurité

- **Validation des entrées** : Prévention injection SQL
- **Transactions** : Atomicité des opérations
- **Logging sécurisé** : Pas de données sensibles dans les logs
- **Variables d'environnement** : Credentials sécurisés

## 📝 API Reference

### Endpoints principaux

- `POST /etl/run` - Lancer pipeline complet
- `POST /etl/extract` - Extraction uniquement  
- `POST /etl/transform` - Transformation uniquement
- `POST /etl/load` - Chargement uniquement
- `GET /etl/status/{job_id}` - Status d'un job
- `GET /etl/reports` - Liste des rapports
- `GET /health` - Health check

### Exemple d'utilisation API

```bash
# Lancer ETL complet
curl -X POST http://localhost:8788/etl/run \
  -H "Content-Type: application/json" \
  -d '{"source_file": "scraped_data.json"}'

# Vérifier le status
curl http://localhost:8788/etl/status/job-123
```

## 🎯 Performance

### Optimisations

- **Batch processing** : Traitement par lots
- **Index database** : Requêtes optimisées
- **Memory management** : Gestion efficace de la RAM
- **Async processing** : Jobs non-bloquants

### Métriques typiques

- **Extraction** : ~1000 records/seconde
- **Transformation** : ~500 records/seconde  
- **Chargement** : ~200 records/seconde
- **Pipeline complet** : ~150 records/seconde

## 📚 Ressources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PostGIS Spatial Database](https://postgis.net/documentation/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose](https://docs.docker.com/compose/)

---

**Note** : Cette documentation couvre la version actuelle du pipeline ETL. Pour les mises à jour, consultez le CHANGELOG.md du projet.
