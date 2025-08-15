# ScrappingBot

Application containerisée de scraping immobilier avec visualisation, monitoring temps réel et intelligence artificielle. Architecture moderne Docker avec microservices, base de données spatiale PostGIS, pipeline ETL, et IA conversationnelle.

## Technologies

- **Docker Multi-Container**: Architecture microservices
- **Base de Données**: PostgreSQL + PostGIS  
- **ETL Pipeline**: Extract-Transform-Load avec validation qualité
- **IA**: Ollama + Chatbot intelligent
- **Scraping**: Playwright avec détection anti-bot
- **API**: FastAPI avec endpoints géospatiaux
- **Frontend**: React + Vite + MapLibre
- **Monitoring**: Grafana + métriques temps réel
- **Cache**: Redis + Nginx reverse proxy

## Installation Rapide

```bash
# Cloner le projet
git clone https://github.com/magicmaxmagic/ScrappingBot.git
cd ScrappingBot

# Construire et lancer
docker-compose build
docker-compose up -d
```

## Services

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | <http://localhost:3000> | Interface web |
| **API** | <http://localhost:8787> | API REST + docs |
| **ETL API** | <http://localhost:8788> | Pipeline ETL + monitoring |
| **Chatbot** | <http://localhost:8080> | Assistant IA |
| **Monitoring** | <http://localhost:3001> | Grafana dashboard |

## Utilisation

### Pipeline ETL (Extract-Transform-Load)

```bash
# Pipeline complet (recommandé)
make etl-full

# Scraping + ETL combiné
make scrape-and-etl

# Validation du pipeline
make etl-validate

# Démonstration avec données d'exemple
make etl-demo

# Status et rapports
make etl-status

# API ETL (service web)
make etl-api
```

### Scraping

```bash
# Scraping automatique via scheduler
docker-compose logs -f scraper

# Scraping manuel
docker-compose exec scraper python database/scraper_adapter.py --where "Montreal" --what "condo"
```

### Base de Données

```bash
# Connexion PostgreSQL
docker-compose exec postgres psql -U scrappingbot_user -d scrappingbot

# Requête spatiale exemple
SELECT title, price FROM listings WHERE ST_DWithin(location, ST_Point(-73.567, 45.501), 5000);
```

### Configuration

Créer un fichier `.env`:

```bash
DATABASE_URL=postgresql://scrappingbot_user:password@postgres:5432/scrappingbot
REDIS_URL=redis://redis:6379
OLLAMA_HOST=http://ollama:11434
PLAYWRIGHT_TIMEOUT_MS=30000
```

## Commandes Make

```bash
# Services principaux
make up-all              # Tous les services avec ETL
make up                  # Services essentiels seulement
make down               # Arrêter tous les services
make restart            # Redémarrer tous les services

# Pipeline ETL
make etl-docker-full    # Pipeline ETL complet dans Docker
make etl-docker-demo    # Démo ETL dans Docker
make etl-docker-test    # Test ETL Docker complet
make etl-build          # Construire image ETL
make etl-logs           # Voir logs ETL

# Base de données  
make db-init            # Initialiser la base
make db-shell           # Shell PostgreSQL
make db-backup          # Sauvegarder
make db-restore         # Restaurer

# Scraping
make scrape-test        # Test de scraping
make scrape-montreal    # Scraper Montreal
make scrape-logs        # Voir logs scraper
make manage

# Monitoring en temps réel
make monitor-live

# Health check complet
make health-full

# État du système
make status

# Logs
make logs
```

## Structure

```
ScrappingBot/
├── docker/              # Configuration Docker et Dockerfiles
├── database/            # Modèles PostgreSQL et migrations  
├── scraper/            # Scrapers Playwright et spiders
├── frontend/           # Interface React et composants
├── workers/            # Workers Cloudflare (legacy)
├── scripts/            # Scripts de gestion et monitoring
│   ├── docker/         # Scripts Docker (health, monitor)
│   └── manage.sh       # Console de gestion interactive
├── docs/               # Documentation
│   └── TROUBLESHOOTING.md
├── config/             # Fichiers de configuration
├── logs/               # Logs des services
├── data/               # Données temporaires
├── docker-compose.yml  # Orchestration des services
└── .env.example        # Template variables d'environnement
```

## Tests

```bash
# Tests automatisés
docker-compose exec api python -m pytest tests/

# Health check
curl http://localhost:8787/health
```

## Production

```bash
# Mode production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Sauvegarde
docker-compose exec postgres pg_dump -U scrappingbot_user scrappingbot > backup.sql
```

## Licence

MIT - Voir LICENSE pour détails.

# API
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Scaling et Performance

```bash
# Scaler le scraper (plusieurs instances)
docker-compose up -d --scale scraper=3

# Monitoring des performances
docker-compose exec grafana grafana-cli admin reset-admin-password admin123
# Puis: http://localhost:3001 (admin/admin123)
```

## Tests et Qualité

### Suite de Tests Automatisés

```bash
# Tests complets de tous les services
make test-docker

# Tests unitaires d'un service
docker-compose exec api python -m pytest tests/

# Tests d'intégration bout-en-bout
docker-compose exec scraper python -m pytest tests/integration/
```

### Monitoring et Observabilité

```bash
# Métriques temps réel
docker-compose exec api curl http://localhost:8787/api/stats

# Logs centralisés avec timestamps
docker-compose logs -f --timestamps

# Alertes personnalisées via Grafana
# http://localhost:3001/alerting/list
```

## Déploiement Production

### Optimisations Recommandées

```bash
# Build optimisé pour production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Sauvegarde automatique de la base de données
docker-compose exec postgres pg_dump -U scrappingbot_user scrappingbot > backup.sql

# SSL/HTTPS avec Let's Encrypt (ajout dans nginx)
# Voir documentation nginx/ pour certificats
```

### Sécurité et Secrets

```bash
# Utiliser Docker Secrets en production
echo "mot_de_passe_securise" | docker secret create db_password -

# Ou variables d'environnement chiffrées
export DATABASE_URL="postgresql://user:$(cat /run/secrets/db_password)@postgres:5432/db"
```

## Cas d'Usage Concrets

### Investisseurs Immobiliers

```bash
# Analyser le marché Montréalais
curl "http://localhost:8787/api/listings?area=montreal&min_price=400000&max_price=800000&property_type=condo"

# Obtenir les statistiques de zone
curl "http://localhost:8787/api/areas/stats"
```

### Développeurs d'Applications

```bash
# API RESTful complète avec géolocalisation
GET /api/listings?bbox=-73.6,45.4,-73.5,45.6  # Requête spatiale
POST /api/listings  # Créer une nouvelle annonce
GET /api/areas/stats  # Métriques par quartier
```

### Analystes de Données

```bash
# Export des données pour analyse
docker-compose exec postgres pg_dump -U scrappingbot_user --table=listings scrappingbot > export.sql

# Connexion directe pour requêtes SQL
docker-compose exec postgres psql -U scrappingbot_user -d scrappingbot
```

## 🤖 Intelligence Artificielle

### Chatbot Conversationnel

Le système inclut un assistant IA capable de :

- **Recherche intelligente** : "Trouve des condos abordables près du métro"
- **Analyse de marché** : "Quel est le prix moyen à Westmount?"
- **Recommandations** : "Suggère-moi des quartiers familiaux"

```bash
# Exemples d'interaction
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Quels sont les meilleurs quartiers pour investir à Montréal?"}'
```

### Modèles LLM Supportés

- **Llama 3.1** (recommandé) - 8B paramètres
- **Mistral 7B** - Alternative rapide
- **CodeLlama** - Pour analyses techniques

## Workflows Automatisés

### Scraping Programmé

```bash
# Le scheduler exécute automatiquement:
# - Scraping quotidien à 6h00
# - Nettoyage hebdomadaire
# - Backups automatiques
# - Alertes de monitoring

# Personnaliser les horaires:
docker-compose exec scheduler crontab -e
```

### Pipeline ETL Intégré

1. **Extract** : Scraping via Playwright
2. **Transform** : Normalisation géospatiale  
3. **Load** : Insertion PostgreSQL+PostGIS

## 📊 Monitoring et Alertes

### Dashboard Grafana

Accédez à http://localhost:3001 pour :

- **Métriques système** : CPU, RAM, stockage
- **Performance scraping** : Temps réponse, taux succès
- **Base de données** : Requêtes/sec, connexions actives
- **Alertes configurables** : Email, Slack, webhook

### Métriques Clés

```bash
# Santé globale du système
curl http://localhost:8787/health | jq .

# Statistiques détaillées
curl http://localhost:8787/api/stats | jq .

# Activité récente
curl http://localhost:8787/api/activity?days=7 | jq .
```

## Sécurité et Éthique

### Scraping Responsable

- **Respect robots.txt** - Vérification automatique
- **Rate limiting** - Délais entre requêtes
- **User-Agent transparent** - Identification claire
- **Détection WAF** - Arrêt automatique si bloqué
- **Pas de contournement** - Respect des protections

### Sécurité des Données

- **Chiffrement** des mots de passe base de données
- **CORS configuré** pour éviter XSS
- **Logs sécurisés** - Pas de données sensibles
- **Backups chiffrés** - Sauvegarde automatique

## Résolution de Problèmes

### Problèmes Courants

```bash
# Service ne démarre pas
docker-compose logs [service-name]

# Base de données inaccessible
docker-compose exec postgres pg_isready

# Espace disque insuffisant
docker system prune -a
docker volume prune

# Conteneur consomme trop de RAM
docker stats
docker-compose restart [service-name]
```

### WAF Détecté (Normal)

```bash
# Le scraper s'arrête automatiquement si bloqué
docker-compose logs scraper | grep "WAF detected"

# Attendre et relancer plus tard
sleep 3600 && docker-compose restart scraper
```

### Performance Lente

```bash
# Optimiser PostgreSQL
docker-compose exec postgres psql -U scrappingbot_user -d scrappingbot -c "REINDEX DATABASE scrappingbot;"

# Vider le cache Redis
docker-compose exec redis redis-cli FLUSHALL

# Redémarrer services
docker-compose restart
```

## Scalabilité

### Horizontal Scaling

```bash
# Multiplier les scrapers
docker-compose up -d --scale scraper=5

# Load balancer API
docker-compose up -d --scale api=3
```

### Optimization Base de Données

```sql
-- Index géospatiaux pour performance
CREATE INDEX idx_listings_location ON listings USING GIST (location);

-- Index sur les prix pour recherches
CREATE INDEX idx_listings_price ON listings (price) WHERE price IS NOT NULL;
```

## Déploiement Multi-Environnement

### Environnement de Développement

```bash
# Mode développement avec hot-reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Production

```bash
# Configuration optimisée production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# SSL/TLS avec certificats
# Configurer nginx/ssl.conf avec Let's Encrypt
```

### Cloud (AWS/GCP/Azure)

```bash
# Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.yml scrappingbot

# Kubernetes
kubectl apply -f k8s/
```

---

## Section Legacy (Méthodes Traditionnelles)

*Cette section conserve les méthodes d'installation traditionnelles pour compatibilité.*

### Installation Manuelle Python

```bash
# 1. Environnement Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Installation Playwright
playwright install

# 3. Base de données locale
# Installer PostgreSQL + PostGIS localement
```

### Scraping Manuel

```bash
# Scraping simple
python3 scraper/spiders/clean_scraper.py --where "montreal" --what "condo"

# Mode debug avec captures
python3 scraper/spiders/clean_scraper.py --where "test" --what "demo" --dom --debug

# URL personnalisée
python3 scraper/spiders/clean_scraper.py \
  --start_url "file://$(pwd)/data/demo_listings.html" \
  --dom --timeout 10000
```

### Frontend Développement

```bash
# Frontend seul
cd frontend
npm install
npm run dev

# API Workers (Cloudflare)
cd workers  
npm install
npx wrangler dev
```

### Tests Manuels

```bash
# Suite de tests Python
python3 scripts/test_suite.py

# Tests spécifiques
python3 scripts/test_suite.py --test waf_detection -v

# Dashboard statique
python3 scripts/generate_dashboard.py
open logs/dashboard.html
```

---

## Contribution

1. Fork le projet sur GitHub
2. Créer une branche feature : `git checkout -b feature/nouvelle-fonctionnalite`
3. Commiter vos changements : `git commit -am 'Ajout nouvelle fonctionnalité'`
4. Pousser vers la branche : `git push origin feature/nouvelle-fonctionnalite`
5. Créer une Pull Request

### Guide de Développement

```bash
# Setup environnement de développement
git clone https://github.com/magicmaxmagic/ScrappingBot.git
cd ScrappingBot

# Lancer en mode dev avec hot-reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Tests avant commit
make test-docker
make lint
```

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

## Démarrage Rapide - Récapitulatif

```bash
# Installation complète en 3 commandes
git clone https://github.com/magicmaxmagic/ScrappingBot.git
cd ScrappingBot
docker-compose up -d

# Vérification que tout fonctionne
curl http://localhost:8787/health
open http://localhost:3000

# Première utilisation
echo "Votre système de scraping immobilier est prêt !"
echo "Dashboard: http://localhost:3000"
echo "Chatbot IA: http://localhost:8080"
echo "Monitoring: http://localhost:3001"
```

**Prêt à révolutionner votre analyse immobilière ? **

---

*ScrappingBot - L'avenir de l'analyse immobilière automatisée* 🏠✨
