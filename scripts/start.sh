#!/usr/bin/env bash
set -euo pipefail

# Lightweight start script (canonical) – prefer this over root duplicate
# Usage: ./scripts/start.sh [service...]
if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: $0 [service ...]"; exit 0; fi

if command -v docker compose >/dev/null 2>&1; then DC="docker compose"; else DC="docker-compose"; fi

if [[ $# -gt 0 ]]; then
  $DC up -d "$@"
else
  $DC up -d
fi
echo "✅ Services démarrés"#!/bin/bash

# ScrappingBot - Démarrage complet du système Docker
# Usage: ./start.sh [service1] [service2] ... ou ./start.sh pour tous les services

set -e

# Configuration
PROJECT_NAME="scrappingbot"
COMPOSE_FILE="docker-compose.yml"

# Services disponibles
AVAILABLE_SERVICES=(
    "postgres"
    "redis" 
    "etl"
    "api"
    "scraper"
    "chatbot"
    "ollama"
    "scheduler"
    "grafana"
    "nginx"
    "frontend"
)

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Fonction pour vérifier Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose n'est pas installé"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker n'est pas en cours d'exécution"
        exit 1
    fi

    log_success "Docker est prêt"
}

# Fonction pour créer les répertoires nécessaires
create_directories() {
    log_info "Création des répertoires nécessaires..."
    
    local dirs=(
        "data"
        "logs"
        "output"
        "config"
        "docker/grafana/dashboards"
        "docker/grafana/provisioning"
        "docker/nginx/ssl"
    )

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_success "Répertoire créé: $dir"
        fi
    done
}

# Fonction pour valider les services
validate_services() {
    local services=("$@")
    local valid_services=()

    if [ ${#services[@]} -eq 0 ]; then
        # Si aucun service spécifié, utiliser tous les services
        valid_services=("${AVAILABLE_SERVICES[@]}")
    else
        for service in "${services[@]}"; do
            if [[ " ${AVAILABLE_SERVICES[@]} " =~ " $service " ]]; then
                valid_services+=("$service")
            else
                log_warning "Service inconnu ignoré: $service"
            fi
        done
    fi

    echo "${valid_services[@]}"
}

# Fonction pour démarrer les services
start_services() {
    local services=("$@")
    
    if [ ${#services[@]} -eq 0 ]; then
        log_info "Démarrage de tous les services..."
        docker-compose up -d
    else
        log_info "Démarrage des services: ${services[*]}"
        docker-compose up -d "${services[@]}"
    fi
}

# Fonction pour afficher le statut
show_status() {
    log_info "Statut des services:"
    docker-compose ps
    
    echo ""
    log_info "Services accessibles:"
    echo "  🌐 Frontend:     http://localhost:3000"
    echo "  🔌 API:          http://localhost:8787"
    echo "  🤖 Chatbot:     http://localhost:8080"
    echo "  ⚙️  ETL:         http://localhost:8788"
    echo "  📊 Grafana:     http://localhost:3001"
    echo "  🧠 Ollama:      http://localhost:11434"
    echo "  🗄️  PostgreSQL: localhost:5432"
    echo "  📦 Redis:       localhost:6379"
}

# Fonction principale
main() {
    log_info "🚀 ScrappingBot - Démarrage du système"
    
    # Vérifications préliminaires
    check_docker
    create_directories
    
    # Validation des services
    local services_to_start
    services_to_start=($(validate_services "$@"))
    
    if [ ${#services_to_start[@]} -eq 0 ]; then
        log_error "Aucun service valide à démarrer"
        exit 1
    fi

    # Construction des images si nécessaire
    log_info "Construction des images Docker..."
    docker-compose build "${services_to_start[@]}"

    # Démarrage des services
    start_services "${services_to_start[@]}"
    
    # Attendre que les services soient prêts
    log_info "Attente que les services soient prêts..."
    sleep 10
    
    # Afficher le statut
    show_status
    
    log_success "🎉 Système ScrappingBot démarré avec succès!"
    log_info "Utilisez 'docker-compose logs -f [service]' pour voir les logs"
    log_info "Utilisez './stop.sh' pour arrêter le système"
}

# Afficher l'aide
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: $0 [service1] [service2] ..."
    echo ""
    echo "Services disponibles:"
    for service in "${AVAILABLE_SERVICES[@]}"; do
        echo "  - $service"
    done
    echo ""
    echo "Exemples:"
    echo "  $0                    # Démarrer tous les services"
    echo "  $0 postgres redis     # Démarrer seulement postgres et redis"
    echo "  $0 etl api            # Démarrer ETL et API"
    exit 0
fi

# Exécuter la fonction principale
main "$@"
