# ETL Docker Service

## 🐳 Configuration Docker

Le service ETL est entièrement containerisé et s'intègre dans l'écosystème Docker du projet.

### Services et Ports

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| ETL API | 8788 | http://localhost:8788 | Service web ETL |
| ETL Docs | 8788 | http://localhost:8788/docs | Documentation API |
| PostgreSQL | 5432 | localhost:5432 | Base de données |
| Redis | 6379 | localhost:6379 | Cache et sessions |

## 🚀 Démarrage rapide

### Option 1: Avec le script automatique
```bash
# Lancement complet avec ETL
./scripts/start-with-etl.sh
```

### Option 2: Avec Make
```bash
# Démarrer tous les services
make up-all

# Ou seulement les services principaux
make up
```

### Option 3: Docker Compose direct
```bash
# Services essentiels avec ETL
docker-compose up -d postgres redis api scraper etl

# Tous les services
docker-compose up -d
```

## 🔧 Commandes ETL Docker

### Construction et gestion des services
```bash
# Construire l'image ETL
make etl-build

# Démarrer le service ETL
make etl-up

# Arrêter le service ETL
make etl-down

# Redémarrer le service ETL
make etl-restart

# Voir les logs
make etl-logs

# Shell dans le container ETL
make etl-shell
```

### Exécution des pipelines
```bash
# Pipeline ETL complet dans Docker
make etl-docker-full

# Démo ETL dans Docker
make etl-docker-demo

# Validation ETL dans Docker
make etl-docker-validate

# Test complet ETL Docker
make etl-docker-test
```

## 📁 Structure Docker

```
docker/
├── Dockerfile.etl              # Image ETL
├── entrypoints/
│   └── etl-entrypoint.sh      # Point d'entrée ETL
docker-compose.yml              # Configuration services
docker-compose.override.yml     # Configuration développement
```

## ⚙️ Configuration

### Variables d'environnement ETL
```env
DATABASE_URL=postgresql://scrappingbot_user:scrappingbot_pass@postgres:5432/scrappingbot
POSTGRES_HOST=postgres
POSTGRES_DB=scrappingbot
POSTGRES_USER=scrappingbot_user
POSTGRES_PASSWORD=scrappingbot_pass
REDIS_URL=redis://redis:6379
ETL_BATCH_SIZE=100
ETL_LOG_LEVEL=INFO
ETL_DATA_PATH=/app/data
ETL_MODE=api
```

### Fichier de configuration
- `config/etl.conf` : Configuration détaillée de l'ETL
- Variables modifiables à chaud
- Paramètres de validation et transformation

## 🔍 Monitoring et debugging

### Health checks
```bash
# Vérifier la santé du service ETL
curl http://localhost:8788/health

# Status de tous les services
docker-compose ps
```

### Logs et debugging
```bash
# Logs ETL en temps réel
docker-compose logs -f etl

# Logs de tous les services
docker-compose logs -f

# Shell interactif dans ETL
docker-compose exec etl bash

# Debugging Python dans le container
docker-compose exec etl python -c "
import sys; sys.path.append('.')
from etl import DataExtractor, DataTransformer, DataValidator
print('ETL modules loaded successfully')
"
```

## 🧪 Tests

### Test automatique complet
```bash
# Lance tous les tests ETL Docker
./scripts/test-etl-docker.sh
```

### Tests manuels
```bash
# Test des composants ETL
docker-compose exec etl python etl/validate.py --component etl

# Test de qualité des données
docker-compose exec etl python etl/validate.py --component quality

# Test de connexion base de données
docker-compose exec etl python etl/validate.py --component database

# Démonstration complète
docker-compose exec etl python etl/demo.py
```

## 🔄 Workflows

### Workflow de développement
1. **Modification du code ETL** → Auto-reload avec volumes montés
2. **Test local** → `make etl-docker-demo`
3. **Validation** → `make etl-docker-validate`
4. **Pipeline complet** → `make etl-docker-full`

### Workflow de production
1. **Build des images** → `docker-compose build etl`
2. **Tests complets** → `make etl-docker-test`
3. **Déploiement** → `docker-compose up -d etl`
4. **Monitoring** → Logs et health checks

## 📊 API ETL

### Endpoints disponibles
- `GET /health` - Health check
- `POST /etl/run` - Lancer pipeline complet
- `POST /etl/extract` - Extraction seule
- `POST /etl/transform` - Transformation seule
- `POST /etl/load` - Chargement seul
- `GET /etl/status/{job_id}` - Status d'un job
- `GET /etl/reports` - Liste des rapports

### Documentation interactive
- URL: http://localhost:8788/docs
- Interface Swagger automatique
- Tests directs des endpoints

## 🔧 Dépannage

### Problèmes courants

1. **Service ETL ne démarre pas**
   ```bash
   # Vérifier les logs
   docker-compose logs etl
   
   # Reconstruire l'image
   make etl-build
   ```

2. **Erreur de connexion base de données**
   ```bash
   # Vérifier PostgreSQL
   docker-compose exec postgres pg_isready -U scrappingbot_user -d scrappingbot
   
   # Redémarrer les services
   docker-compose restart postgres etl
   ```

3. **API ETL ne répond pas**
   ```bash
   # Vérifier le port
   netstat -tulnp | grep 8788
   
   # Tester la connexion
   curl http://localhost:8788/health
   ```

4. **Problèmes de permissions**
   ```bash
   # Vérifier les volumes
   docker-compose exec etl ls -la /app/data /app/logs
   
   # Corriger les permissions
   sudo chmod -R 755 data logs
   ```

## 📈 Performance

### Métriques typiques (Docker)
- **Démarrage service**: ~15-20 secondes
- **Pipeline complet**: ~30-60 secondes (selon données)
- **Mémoire utilisée**: ~200-500MB
- **CPU**: ~10-20% pendant traitement

### Optimisations
- Utilisation de volumes pour persistance
- Cache Redis pour optimiser les requêtes
- Traitement par lots configurables
- Connexions base de données poolées

## 🚀 Production

### Configuration recommandée
```yaml
etl:
  deploy:
    replicas: 1
    resources:
      limits:
        memory: 1G
        cpus: '0.5'
      reservations:
        memory: 512M
        cpus: '0.25'
```

### Monitoring production
- Intégration avec Grafana
- Alertes sur échecs de pipeline
- Métriques de performance
- Logs centralisés

---

**Note**: Pour la documentation complète de l'ETL, consultez `etl/README.md`.
