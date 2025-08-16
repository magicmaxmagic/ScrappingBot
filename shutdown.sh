#!/bin/bash

# ScrappingBot Graceful Shutdown Script
# Arrêt propre de tous les services avec sauvegarde

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 ScrappingBot - Arrêt gracieux${NC}"
echo "====================================="

# Function to log messages
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    case $level in
        "INFO")
            echo -e "${BLUE}[$timestamp] INFO:${NC} $message"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[$timestamp] SUCCESS:${NC} $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}[$timestamp] WARNING:${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[$timestamp] ERROR:${NC} $message"
            ;;
    esac
}

# Function to check if services are running
check_services() {
    if ! docker-compose ps -q | grep -q .; then
        log "INFO" "Aucun service en cours d'exécution"
        exit 0
    fi
}

# Function to backup data
backup_data() {
    log "INFO" "💾 Sauvegarde des données avant arrêt..."
    
    local backup_dir="data/backup"
    local timestamp=$(date "+%Y%m%d_%H%M%S")
    
    mkdir -p "$backup_dir"
    
    # Backup database if postgres is running
    if docker-compose ps postgres | grep -q "Up"; then
        log "INFO" "Sauvegarde de PostgreSQL..."
        if docker-compose exec -T postgres pg_dump -U scrappingbot_user scrappingbot > "${backup_dir}/postgres_${timestamp}.sql" 2>/dev/null; then
            log "SUCCESS" "Base de données sauvegardée: postgres_${timestamp}.sql"
        else
            log "WARNING" "Échec de la sauvegarde PostgreSQL"
        fi
    fi
    
    # Backup Redis data if redis is running
    if docker-compose ps redis | grep -q "Up"; then
        log "INFO" "Sauvegarde de Redis..."
        if docker-compose exec -T redis redis-cli BGSAVE >/dev/null 2>&1; then
            sleep 2  # Wait for background save to complete
            log "SUCCESS" "Données Redis sauvegardées"
        else
            log "WARNING" "Échec de la sauvegarde Redis"
        fi
    fi
    
    # Backup logs
    if docker-compose logs > "${backup_dir}/logs_${timestamp}.txt" 2>/dev/null; then
        log "SUCCESS" "Logs sauvegardés: logs_${timestamp}.txt"
    fi
}

# Function to gracefully stop services
graceful_stop() {
    log "INFO" "⏳ Arrêt gracieux des services..."
    
    # Stop services in reverse order of dependency
    services_order=(
        "nginx"
        "grafana"
        "frontend"
        "chatbot"
        "ollama"
        "scheduler"
        "scraper"
        "api"
        "etl"
        "redis"
        "postgres"
    )
    
    for service in "${services_order[@]}"; do
        if docker-compose ps "$service" | grep -q "Up"; then
            log "INFO" "Arrêt de $service..."
            
            # Send graceful shutdown signal
            docker-compose stop -t 30 "$service" 2>/dev/null || {
                log "WARNING" "Arrêt forcé de $service"
                docker-compose kill "$service" 2>/dev/null || true
            }
            
            log "SUCCESS" "$service arrêté"
        fi
    done
}

# Function to cleanup containers and networks
cleanup() {
    log "INFO" "🧹 Nettoyage des ressources..."
    
    # Remove containers
    if docker-compose down --remove-orphans >/dev/null 2>&1; then
        log "SUCCESS" "Containers supprimés"
    else
        log "WARNING" "Problème lors de la suppression des containers"
    fi
    
    # Optional: Remove volumes (only if --remove-volumes flag is passed)
    if [ "$REMOVE_VOLUMES" = "true" ]; then
        log "WARNING" "Suppression des volumes de données..."
        if docker-compose down -v >/dev/null 2>&1; then
            log "SUCCESS" "Volumes supprimés"
        else
            log "WARNING" "Problème lors de la suppression des volumes"
        fi
    fi
    
    # Remove dangling images if requested
    if [ "$CLEANUP_IMAGES" = "true" ]; then
        log "INFO" "Nettoyage des images inutilisées..."
        if docker image prune -f >/dev/null 2>&1; then
            log "SUCCESS" "Images inutilisées supprimées"
        fi
    fi
}

# Function to show shutdown summary
show_summary() {
    log "SUCCESS" "✅ Arrêt terminé"
    echo ""
    echo -e "${GREEN}┌─ Résumé de l'arrêt ─────────────────────────────────────┐${NC}"
    echo -e "${GREEN}│${NC}"
    
    if [ -d "data/backup" ]; then
        local backup_count=$(find data/backup -name "*.sql" -o -name "*.txt" | wc -l)
        echo -e "${GREEN}│${NC} ${BLUE}Sauvegardes créées:${NC} $backup_count fichiers"
    fi
    
    echo -e "${GREEN}│${NC} ${BLUE}Containers arrêtés:${NC} Tous"
    echo -e "${GREEN}│${NC} ${BLUE}Networks supprimés:${NC} Oui"
    
    if [ "$REMOVE_VOLUMES" = "true" ]; then
        echo -e "${GREEN}│${NC} ${BLUE}Volumes supprimés:${NC} Oui"
    else
        echo -e "${GREEN}│${NC} ${BLUE}Volumes conservés:${NC} Oui"
    fi
    
    echo -e "${GREEN}│${NC}"
    echo -e "${GREEN}│${NC} ${YELLOW}Pour redémarrer:${NC} ./deploy.sh"
    echo -e "${GREEN}│${NC} ${YELLOW}Sauvegardes:${NC}     data/backup/"
    echo -e "${GREEN}│${NC}"
    echo -e "${GREEN}└─────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Afficher cette aide"
    echo "  -f, --force             Arrêt forcé sans sauvegarde"
    echo "  -v, --remove-volumes    Supprimer les volumes de données"
    echo "  -i, --cleanup-images    Nettoyer les images inutilisées"
    echo "  -q, --quiet             Mode silencieux"
    echo ""
    echo "Exemples:"
    echo "  $0                      # Arrêt standard avec sauvegarde"
    echo "  $0 -f                   # Arrêt forcé rapide"
    echo "  $0 -v -i               # Arrêt avec suppression complète"
    echo ""
}

# Parse command line arguments
FORCE_SHUTDOWN=false
REMOVE_VOLUMES=false
CLEANUP_IMAGES=false
QUIET_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -f|--force)
            FORCE_SHUTDOWN=true
            shift
            ;;
        -v|--remove-volumes)
            REMOVE_VOLUMES=true
            shift
            ;;
        -i|--cleanup-images)
            CLEANUP_IMAGES=true
            shift
            ;;
        -q|--quiet)
            QUIET_MODE=true
            shift
            ;;
        *)
            echo "Option inconnue: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Redirect output if quiet mode
if [ "$QUIET_MODE" = "true" ]; then
    exec > /tmp/shutdown.log 2>&1
fi

# Confirmation for destructive operations
if [ "$REMOVE_VOLUMES" = "true" ] && [ "$FORCE_SHUTDOWN" = "false" ]; then
    echo -e "${YELLOW}⚠️  ATTENTION: Cette opération supprimera TOUTES les données !${NC}"
    echo -e "${YELLOW}   Base de données, cache Redis, logs... tout sera perdu.${NC}"
    echo ""
    read -p "Êtes-vous sûr de vouloir continuer ? (tapez 'YES' pour confirmer): " confirm
    
    if [ "$confirm" != "YES" ]; then
        log "INFO" "Opération annulée par l'utilisateur"
        exit 0
    fi
fi

# Check if Docker is available
if ! command -v docker >/dev/null 2>&1; then
    log "ERROR" "Docker n'est pas disponible"
    exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1; then
    log "ERROR" "Docker Compose n'est pas disponible"
    exit 1
fi

# Main shutdown sequence
main() {
    local start_time=$(date +%s)
    
    # Check if services are running
    check_services
    
    # Backup data unless force mode
    if [ "$FORCE_SHUTDOWN" = "false" ]; then
        backup_data
    else
        log "INFO" "Mode forcé - pas de sauvegarde"
    fi
    
    # Stop services gracefully
    graceful_stop
    
    # Cleanup resources
    cleanup
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log "INFO" "Arrêt terminé en ${duration}s"
    
    # Show summary unless quiet mode
    if [ "$QUIET_MODE" = "false" ]; then
        show_summary
    fi
}

# Execute main function
main
