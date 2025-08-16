# 🎯 ScrappingBot - Scripts et Outils de Déploiement

Ce document présente tous les scripts et outils créés pour le déploiement et la gestion de ScrappingBot.

## 📁 Structure des Scripts

```
ScrappingBot/
├── deploy.sh                 # 🚀 Déploiement automatisé complet
├── shutdown.sh               # 🛑 Arrêt gracieux avec sauvegarde
├── Makefile.docker           # 🔧 Commandes Docker simplifiées
├── scripts/
│   ├── health-check.sh       # 🏥 Vérification de santé complète
│   ├── monitor.sh            # 📊 Monitoring en temps réel
│   ├── start.sh              # ▶️  Démarrage simple
│   └── stop.sh               # ⏹️  Arrêt simple
├── docker/
│   └── redis/
│       └── redis.conf        # ⚙️  Configuration Redis optimisée
└── docs/
    └── DOCKER.md             # 📖 Guide Docker complet
```

## 🚀 Scripts Principaux

### 1. `deploy.sh` - Déploiement Automatisé
**Fonction** : Déploiement complet avec validation et monitoring
**Usage** :
```bash
./deploy.sh                    # Déploiement production
./deploy.sh --mode development # Mode développement
./deploy.sh --timeout 300      # Timeout personnalisé
```

**Fonctionnalités** :
- ✅ Vérification des prérequis (Docker, docker-compose, espace disque)
- 🔧 Création automatique du fichier `.env` avec mots de passe sécurisés
- 🏗️ Construction des images Docker en parallèle
- 🔄 Démarrage orchestré des services (base → traitement → web → monitoring)
- 🏥 Vérifications de santé automatiques
- 📊 Résumé du déploiement avec URLs d'accès

### 2. `shutdown.sh` - Arrêt Gracieux
**Fonction** : Arrêt propre avec sauvegarde automatique
**Usage** :
```bash
./shutdown.sh                  # Arrêt standard
./shutdown.sh -f               # Arrêt forcé rapide
./shutdown.sh -v               # Avec suppression des volumes
./shutdown.sh -i               # Avec nettoyage des images
```

**Fonctionnalités** :
- 💾 Sauvegarde automatique PostgreSQL et Redis
- 🔄 Arrêt en ordre inverse des dépendances
- 🧹 Nettoyage optionnel des ressources
- 📝 Logs de sauvegarde horodatés
- ⚠️ Confirmation pour les opérations destructives

## 🔧 Outils de Gestion

### 3. `Makefile.docker` - Interface Simplifiée
**Fonction** : Commandes Docker simplifiées avec interface colorée
**Usage** :
```bash
make -f Makefile.docker help   # Voir toutes les commandes
make -f Makefile.docker deploy # Déploiement complet
make -f Makefile.docker dev    # Mode développement
```

**Commandes principales** :
```bash
# Construction
build, build-etl, build-api, build-scraper

# Gestion des services
up, up-core, up-etl, down, restart

# Monitoring
status, health, logs, logs-etl, monitor

# Accès aux containers
exec-etl, exec-postgres, exec-redis

# Maintenance
backup-db, restore-db, clean
```

### 4. `scripts/health-check.sh` - Diagnostic Système
**Fonction** : Vérification complète de la santé des services
**Usage** :
```bash
./scripts/health-check.sh      # Vérification complète
```

**Tests effectués** :
- 🐳 État des containers Docker
- 🔌 Connectivité réseau (ports TCP)
- 🌐 Endpoints HTTP (API, ETL, Frontend)
- 🗄️ Connectivité base de données PostgreSQL
- 🔴 Connectivité cache Redis
- ⚙️ Fonctionnalité des modules ETL
- 📊 Rapport de santé avec pourcentage de réussite

### 5. `scripts/monitor.sh` - Surveillance Temps Réel
**Fonction** : Monitoring interactif des services
**Usage** :
```bash
./scripts/monitor.sh           # Monitoring de base
./scripts/monitor.sh -l etl    # Avec logs ETL
./scripts/monitor.sh -i 10 -l api -n 20  # Config avancée
```

**Affichage** :
- 📦 État des containers
- 📊 Utilisation des ressources (CPU, RAM, Réseau)
- 🌐 État des connexions réseau
- 💾 Utilisation de l'espace disque Docker
- 📈 Métriques applicatives (Redis, PostgreSQL)
- 📝 Logs en temps réel (optionnel)

## ⚙️ Configurations

### 6. `docker/redis/redis.conf` - Redis Optimisé
**Configuration** : Redis optimisé pour cache et sessions
**Optimisations** :
- 💾 Limite mémoire 256MB avec éviction LRU
- 💿 Persistence AOF + RDB
- 🔒 Sécurité (commandes dangereuses désactivées)
- ⚡ Performance tuning (compression, rehashing)

### 7. `docker-compose.yml` - Architecture Complète
**Services** :
- `postgres` : Base de données avec PostGIS
- `redis` : Cache et sessions
- `etl` : Pipeline de traitement
- `api` : API REST FastAPI
- `frontend` : Interface React/Next.js
- `scraper` : Bot de scraping
- `chatbot` : Interface conversationnelle
- `grafana` : Monitoring et dashboards

**Améliorations** :
- 🔧 Variables d'environnement `.env`
- 🏥 Health checks robustes
- 📊 Limites de ressources
- 🔄 Restart policies
- 🌐 Réseau isolé

## 📊 Monitoring et Observabilité

### URLs d'Accès
```bash
Frontend:     http://localhost:3000
API:          http://localhost:8787
ETL:          http://localhost:8788
Chatbot:      http://localhost:8080
Grafana:      http://localhost:3001
PostgreSQL:   localhost:5432
Redis:        localhost:6379
```

### Commandes de Diagnostic
```bash
# Status général
docker-compose ps

# Logs en temps réel
docker-compose logs -f

# Utilisation des ressources
docker stats

# Santé des services
./scripts/health-check.sh

# Monitoring interactif
./scripts/monitor.sh
```

## 🔄 Workflows Typiques

### Déploiement Initial
```bash
# 1. Cloner le repo
git clone <repository>
cd ScrappingBot

# 2. Déploiement automatisé
./deploy.sh

# 3. Vérifier le déploiement
./scripts/health-check.sh

# 4. Monitoring (optionnel)
./scripts/monitor.sh -l etl
```

### Développement Quotidien
```bash
# Démarrer en mode développement
make -f Makefile.docker dev

# Voir les logs ETL
make -f Makefile.docker logs-etl

# Tests
make -f Makefile.docker test-docker

# Redémarrer un service
make -f Makefile.docker restart-etl
```

### Maintenance
```bash
# Sauvegarde
make -f Makefile.docker backup-db

# Mise à jour
make -f Makefile.docker down
make -f Makefile.docker build
make -f Makefile.docker up

# Nettoyage
make -f Makefile.docker clean
```

### Arrêt et Sauvegarde
```bash
# Arrêt standard avec sauvegarde
./shutdown.sh

# Arrêt rapide sans sauvegarde
./shutdown.sh -f

# Arrêt avec suppression complète
./shutdown.sh -v -i
```

## 🛠️ Personnalisation

### Variables d'Environnement
Créer un fichier `.env` :
```bash
POSTGRES_PASSWORD=mon_mot_de_passe
API_SECRET_KEY=ma_clé_secrète
LOG_LEVEL=DEBUG
ETL_BATCH_SIZE=500
```

### Modification des Ports
Dans `docker-compose.yml` :
```yaml
services:
  api:
    ports:
      - "8080:8787"  # Changer port externe
```

### Ajout de Services
1. Ajouter le service dans `docker-compose.yml`
2. Créer le Dockerfile dans `docker/`
3. Ajouter les commandes dans `Makefile.docker`
4. Mettre à jour les scripts de monitoring

## 🚨 Dépannage

### Problèmes Courants
```bash
# Service ne démarre pas
docker-compose logs [service]

# Port occupé
netstat -tulpn | grep [port]
sudo lsof -i :[port]

# Espace disque insuffisant
docker system df
docker system prune -f

# Permissions
chmod +x scripts/*.sh deploy.sh shutdown.sh
```

### Diagnostic Automatisé
```bash
# Vérification complète
./scripts/health-check.sh

# Test de connectivité
curl http://localhost:8787/health
curl http://localhost:8788/health
```

## 📚 Documentation Complète

- 📖 **Guide Docker** : `docs/DOCKER.md`
- 🔧 **Configuration** : `.env.example`
- 🧪 **Tests** : `tests/README.md`
- 📊 **Monitoring** : `docs/MONITORING.md`

---

🎉 **Félicitations !** Vous avez maintenant une suite complète d'outils pour gérer ScrappingBot en production.
