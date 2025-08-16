#!/bin/bash

# ScrappingBot - Arrêt du système Docker
# Usage: ./stop.sh [clean]

set -e

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

# Fonction principale
main() {
    log_info "🛑 Arrêt du système ScrappingBot"

    # Arrêt des services
    log_info "Arrêt des containers..."
    docker-compose down

    if [[ "$1" == "clean" ]]; then
        log_warning "Nettoyage complet demandé..."
        
        # Supprimer les volumes (attention: cela supprime les données!)
        log_warning "Suppression des volumes Docker (données perdues!)"
        docker-compose down -v
        
        # Supprimer les images
        log_info "Suppression des images Docker..."
        docker-compose down --rmi all
        
        # Nettoyer les images orphelines
        log_info "Nettoyage des images orphelines..."
        docker system prune -f
        
        log_warning "Nettoyage complet terminé - toutes les données ont été supprimées!"
    else
        log_info "Arrêt normal - les données sont conservées"
        log_info "Utilisez './stop.sh clean' pour un nettoyage complet"
    fi

    log_success "🎉 Système ScrappingBot arrêté"
}

# Afficher l'aide
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: $0 [clean]"
    echo ""
    echo "Options:"
    echo "  clean    Arrêt complet avec suppression des volumes et images"
    echo ""
    echo "Exemples:"
    echo "  $0           # Arrêt normal (données conservées)"
    echo "  $0 clean     # Arrêt avec nettoyage complet"
    exit 0
fi

main "$@"
