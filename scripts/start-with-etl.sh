#!/bin/bash

# Script de lancement complet avec ETL
set -e

echo "🚀 Lancement de ScrappingBot avec ETL"
echo "===================================="

# Variables
SERVICES=(postgres redis scraper api etl)
OPTIONAL_SERVICES=(chatbot ollama frontend nginx)

# Fonction pour vérifier la santé d'un service
check_service_health() {
    local service=$1
    echo "🔍 Vérification de la santé de $service..."
    
    case $service in
        "postgres")
            docker-compose exec postgres pg_isready -U scrappingbot_user -d scrappingbot > /dev/null
            ;;
        "redis")
            docker-compose exec redis redis-cli ping > /dev/null
            ;;
        "etl")
            # Vérifier si l'API ETL répond
            curl -s http://localhost:8788/health > /dev/null || return 1
            ;;
        *)
            # Pour les autres services, vérifier juste qu'ils tournent
            docker-compose ps $service | grep "Up" > /dev/null
            ;;
    esac
}

# Construire toutes les images
echo "🔨 Construction des images Docker..."
docker-compose build "${SERVICES[@]}"

# Lancer les services essentiels
echo "🚀 Lancement des services essentiels..."
docker-compose up -d "${SERVICES[@]}"

# Attendre que les services soient prêts
echo "⏳ Attente que les services soient prêts..."
sleep 15

# Vérifier la santé des services
echo "🏥 Vérification de la santé des services..."
for service in "${SERVICES[@]}"; do
    if check_service_health "$service"; then
        echo "✅ $service est en bonne santé"
    else
        echo "⚠️  $service ne répond pas encore"
    fi
done

# Tests ETL rapides
echo "🧪 Tests ETL rapides..."
echo "  - Test des composants ETL..."
if docker-compose exec etl python etl/validate.py --component etl; then
    echo "  ✅ Composants ETL fonctionnels"
else
    echo "  ⚠️ Problèmes avec les composants ETL"
fi

# Afficher l'état des services
echo ""
echo "📋 État des services:"
docker-compose ps

echo ""
echo "🎯 Services actifs:"
echo "   - PostgreSQL: localhost:5432"
echo "   - Redis: localhost:6379"  
echo "   - API: http://localhost:8787"
echo "   - ETL API: http://localhost:8788"
echo "   - ETL API Docs: http://localhost:8788/docs"

echo ""
echo "🔧 Commandes utiles:"
echo "   - Voir tous les logs: docker-compose logs -f"
echo "   - Voir les logs ETL: make etl-logs"
echo "   - Pipeline ETL complet: make etl-docker-full"
echo "   - Test ETL: make etl-docker-test"
echo "   - Demo ETL: make etl-docker-demo"
echo "   - Arrêter tous les services: docker-compose down"

echo ""
echo "✅ ScrappingBot avec ETL est prêt!"

# Optionnel: lancer les services supplémentaires
read -p "🤔 Voulez-vous lancer les services optionnels (chatbot, frontend, nginx)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Lancement des services optionnels..."
    docker-compose up -d "${OPTIONAL_SERVICES[@]}"
    sleep 10
    
    echo ""
    echo "🎯 Services supplémentaires actifs:"
    echo "   - Chatbot: http://localhost:8080"
    echo "   - Frontend: http://localhost:3000"
    echo "   - Nginx: http://localhost:80"
fi

echo ""
echo "🎉 Tous les services sont lancés!"
