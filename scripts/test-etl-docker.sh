#!/bin/bash

# Script de test pour le service ETL Docker
set -e

echo "🚀 Test du service ETL Docker"
echo "=============================="

# Variables
CONTAINER_NAME="scrappingbot-etl"
NETWORK_NAME="scrappingbot_scrappingbot-network"

# Fonction pour vérifier si un container existe
container_exists() {
    docker ps -a --format "table {{.Names}}" | grep -q "^${1}$"
}

# Fonction pour vérifier si un container est en cours d'exécution
container_running() {
    docker ps --format "table {{.Names}}" | grep -q "^${1}$"
}

echo "📋 Vérification de l'état des services..."

# Vérifier PostgreSQL
if container_running "scrappingbot-postgres"; then
    echo "✅ PostgreSQL est en cours d'exécution"
else
    echo "❌ PostgreSQL n'est pas en cours d'exécution"
    echo "   Lancement avec: docker-compose up -d postgres"
    exit 1
fi

# Construire l'image ETL si nécessaire
echo "🔨 Construction de l'image ETL..."
docker-compose build etl

# Lancer le service ETL
echo "🚀 Lancement du service ETL..."
docker-compose up -d etl

# Attendre que le service soit prêt
echo "⏳ Attendre que le service ETL soit prêt..."
sleep 10

# Vérifier que le container est en cours d'exécution
if container_running "$CONTAINER_NAME"; then
    echo "✅ Service ETL en cours d'exécution"
else
    echo "❌ Service ETL n'a pas pu démarrer"
    echo "Logs du container:"
    docker-compose logs etl
    exit 1
fi

# Test de l'API ETL (si disponible)
echo "🧪 Test de l'API ETL..."
if curl -s http://localhost:8788/health > /dev/null 2>&1; then
    echo "✅ API ETL répond sur le port 8788"
    
    # Test des endpoints
    echo "🔍 Test des endpoints ETL..."
    
    # Health check
    HEALTH=$(curl -s http://localhost:8788/health)
    echo "   Health: $HEALTH"
    
    # List reports
    REPORTS=$(curl -s http://localhost:8788/etl/reports)
    echo "   Reports disponibles: $(echo $REPORTS | jq -r 'length // 0') rapports"
    
else
    echo "⚠️  API ETL ne répond pas encore (normal si juste démarré)"
fi

# Test de validation ETL
echo "🔍 Test de validation ETL..."
docker-compose exec etl python etl/validate.py --component etl

# Test du demo ETL
echo "🎭 Test du démo ETL..."
docker-compose exec etl python etl/demo.py

# Afficher les logs récents
echo "📋 Logs récents du service ETL:"
docker-compose logs --tail=20 etl

echo ""
echo "✅ Tests du service ETL terminés!"
echo ""
echo "🔧 Commandes utiles:"
echo "   - Voir les logs: docker-compose logs -f etl"
echo "   - Arrêter le service: docker-compose stop etl"
echo "   - Redémarrer: docker-compose restart etl"
echo "   - Shell dans le container: docker-compose exec etl bash"
echo "   - Pipeline ETL complet: docker-compose exec etl python etl/orchestrator.py --full"
echo "   - API ETL: http://localhost:8788"
