# 🐳 ScrappingBot - Guide Docker

Ce guide vous explique comment utiliser Docker pour déployer et gérer l'application ScrappingBot.

## 📋 Prérequis

- Docker Desktop (macOS/Windows) ou Docker Engine (Linux)
- Docker Compose v2.0+
- Au moins 4GB de RAM disponible
- 10GB d'espace disque libre

### Installation Docker sur macOS
```bash
# Via Homebrew
brew install docker docker-compose

# Ou télécharger Docker Desktop depuis https://docker.com
```

## 🚀 Démarrage rapide

### 1. Démarrage complet
```bash
# Construction et démarrage de tous les services
make -f Makefile.docker deploy

# Ou manuellement
docker-compose up -d --build
```

### 2. Vérification du déploiement
```bash
# Vérifier le statut des services
make -f Makefile.docker status

# Vérification de santé complète
./scripts/health-check.sh
```

### 3. Monitoring en temps réel
```bash
# Monitoring de base
./scripts/monitor.sh

# Monitoring avec logs ETL
./scripts/monitor.sh -l etl

# Monitoring avancé (intervalle 10s, logs API, 20 lignes)
./scripts/monitor.sh -i 10 -l api -n 20
```

## 🏗️ Architecture des services

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │       API       │    │      ETL        │
│   (React/Next)  │◄───┤   (FastAPI)     │◄───┤   (Python)      │
│   Port: 3000    │    │   Port: 8787    │    │   Port: 8788    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │     Redis       │              │
         └──────────────┤   (Cache)       │◄─────────────┘
                        │   Port: 6379    │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   PostgreSQL    │
                        │  (Database)     │
                        │   Port: 5432    │
                        └─────────────────┘
```

### Services disponibles

| Service | Description | Port | Santé |
|---------|-------------|------|-------|
| **frontend** | Interface utilisateur React/Next.js | 3000 | http://localhost:3000 |
| **api** | API REST FastAPI | 8787 | http://localhost:8787/health |
| **etl** | Pipeline de traitement des données | 8788 | http://localhost:8788/health |
| **scraper** | Bot de scraping Scrapy/Playwright | - | Logs uniquement |
| **chatbot** | Interface conversationnelle | 8080 | http://localhost:8080 |
| **postgres** | Base de données principale | 5432 | Interne |
| **redis** | Cache et queue de tâches | 6379 | Interne |
| **grafana** | Monitoring et dashboards | 3001 | http://localhost:3001 |
| **ollama** | LLM local | 11434 | http://localhost:11434 |

## 📖 Commandes Makefile

Le fichier `Makefile.docker` contient toutes les commandes utiles :

### Construction et déploiement
```bash
# Construire toutes les images
make -f Makefile.docker build

# Construire une image spécifique
make -f Makefile.docker build-etl
make -f Makefile.docker build-api

# Déploiement complet
make -f Makefile.docker deploy
```

### Gestion des services
```bash
# Démarrer tous les services
make -f Makefile.docker up

# Démarrer les services de base uniquement
make -f Makefile.docker up-core

# Démarrer ETL avec ses dépendances
make -f Makefile.docker up-etl

# Arrêter tous les services
make -f Makefile.docker down

# Redémarrer tous les services
make -f Makefile.docker restart
```

### Monitoring et logs
```bash
# Afficher le statut
make -f Makefile.docker status

# Vérifier la santé des services
make -f Makefile.docker health

# Voir les logs
make -f Makefile.docker logs
make -f Makefile.docker logs-etl
make -f Makefile.docker logs-api
```

### Accès aux containers
```bash
# Shell dans le container ETL
make -f Makefile.docker exec-etl

# Shell PostgreSQL
make -f Makefile.docker exec-postgres

# Shell Redis
make -f Makefile.docker exec-redis
```

## 🔧 Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine :

```bash
# Base de données
POSTGRES_DB=scrappingbot
POSTGRES_USER=scrappingbot_user
POSTGRES_PASSWORD=secure_password_here
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# API
API_HOST=0.0.0.0
API_PORT=8787
API_SECRET_KEY=your_secret_key_here

# ETL
ETL_HOST=0.0.0.0
ETL_PORT=8788
ETL_BATCH_SIZE=1000

# Scraping
SCRAPER_USER_AGENT=ScrappingBot/1.0
SCRAPER_DELAY=1

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Personnalisation des ports

Modifiez le fichier `docker-compose.yml` pour changer les ports :

```yaml
services:
  api:
    ports:
      - "8787:8787"  # host:container
```

## 🧪 Tests et développement

### Mode développement
```bash
# Démarrer uniquement les services de base
make -f Makefile.docker dev

# Exécuter les tests ETL
make -f Makefile.docker test-docker

# Test rapide
make -f Makefile.docker quick-test
```

### Tests unitaires dans Docker
```bash
# Tests ETL complets
docker-compose exec etl python -m pytest tests/ -v

# Tests spécifiques
docker-compose exec etl python -m pytest tests/test_normalize.py -v

# Tests avec coverage
docker-compose exec etl python -m pytest tests/ --cov=etl --cov-report=html
```

## 🗄️ Gestion de la base de données

### Sauvegarde
```bash
# Sauvegarde automatique
make -f Makefile.docker backup-db

# Sauvegarde manuelle
docker-compose exec postgres pg_dump -U scrappingbot_user scrappingbot > backup.sql
```

### Restauration
```bash
# Restauration via Makefile
make -f Makefile.docker restore-db FILE=backup.sql

# Restauration manuelle
docker-compose exec -T postgres psql -U scrappingbot_user -d scrappingbot < backup.sql
```

### Migrations
```bash
# Exécuter les migrations Alembic
docker-compose exec etl alembic upgrade head

# Créer une nouvelle migration
docker-compose exec etl alembic revision --autogenerate -m "Description"
```

## 📊 Monitoring et observabilité

### Grafana Dashboard
```bash
# Ouvrir Grafana
make -f Makefile.docker monitor

# Credentials par défaut:
# Username: admin
# Password: admin
```

### Logs centralisés
```bash
# Logs en temps réel
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs -f etl

# Logs avec timestamps
docker-compose logs -f -t
```

### Métriques système
```bash
# Utilisation des ressources
docker stats

# Espace disque Docker
docker system df

# Nettoyage des ressources
docker system prune -f
```

## 🚨 Dépannage

### Problèmes courants

#### Service ne démarre pas
```bash
# Vérifier les logs
docker-compose logs [service_name]

# Vérifier la configuration
docker-compose config

# Redémarrer un service
docker-compose restart [service_name]
```

#### Problèmes de connectivité
```bash
# Tester la connectivité réseau
docker-compose exec etl ping postgres
docker-compose exec etl ping redis

# Vérifier les ports
netstat -tulpn | grep [port_number]
```

#### Base de données corrompue
```bash
# Réinitialiser la base de données
docker-compose down
docker volume rm scrappingbot_postgres_data
docker-compose up -d postgres
```

#### Problèmes de permissions
```bash
# Changer les permissions des scripts
chmod +x scripts/*.sh

# Problèmes Docker sur Linux
sudo usermod -aG docker $USER
newgrp docker
```

### Diagnostic automatique
```bash
# Script de diagnostic complet
./scripts/health-check.sh

# Vérification rapide
curl http://localhost:8787/health
curl http://localhost:8788/health
```

## 🔄 Mise à jour

### Mise à jour des images
```bash
# Reconstruire toutes les images
make -f Makefile.docker build

# Mise à jour avec redémarrage
make -f Makefile.docker down
make -f Makefile.docker build
make -f Makefile.docker up
```

### Mise à jour des dépendances
```bash
# Mettre à jour requirements.txt
# Puis reconstruire l'image ETL
make -f Makefile.docker build-etl
```

## 🧹 Nettoyage

### Nettoyage standard
```bash
# Arrêter et supprimer les containers
make -f Makefile.docker down

# Nettoyage complet
make -f Makefile.docker clean
```

### Nettoyage avancé
```bash
# Supprimer tous les containers arrêtés
docker container prune -f

# Supprimer toutes les images non utilisées
docker image prune -a -f

# Supprimer tous les volumes non utilisés
docker volume prune -f

# Nettoyage système complet
docker system prune -a -f --volumes
```

## 📚 Ressources supplémentaires

- [Documentation Docker](https://docs.docker.com/)
- [Documentation Docker Compose](https://docs.docker.com/compose/)
- [Best Practices Docker](https://docs.docker.com/develop/dev-best-practices/)
- [Guide de sécurité Docker](https://docs.docker.com/engine/security/)

---

💡 **Conseil** : Utilisez `./scripts/monitor.sh` pour surveiller vos services en temps réel pendant le développement !

🔍 **Aide** : Pour toute question, exécutez `make -f Makefile.docker help` pour voir toutes les commandes disponibles.
