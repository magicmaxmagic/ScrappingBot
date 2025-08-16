#!/bin/bash

# Script de gestion des logs pour ScrappingBot
# Utilisation: ./scripts/manage-logs.sh [command] [options]

LOG_DIR="./logs"
DATE=$(date +%Y-%m-%d)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_usage() {
    echo -e "${BLUE}ScrappingBot - Gestionnaire de Logs${NC}"
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  show [SERVICE]     - Afficher les logs (all, api, frontend, scraper, etl, chatbot, database)"
    echo "  tail [SERVICE]     - Suivre les logs en temps réel"
    echo "  clean [DAYS]       - Nettoyer les logs plus anciens que X jours (défaut: 7)"
    echo "  size              - Afficher la taille des logs par service"
    echo "  backup            - Sauvegarder les logs actuels"
    echo "  rotate            - Faire la rotation des logs"
    echo ""
    echo "Examples:"
    echo "  $0 show api       - Afficher les logs de l'API"
    echo "  $0 tail all       - Suivre tous les logs"
    echo "  $0 clean 30       - Supprimer les logs de plus de 30 jours"
}

show_logs() {
    local service=${1:-"all"}
    
    if [ "$service" = "all" ]; then
        echo -e "${BLUE}📋 Affichage de tous les logs récents${NC}"
        for dir in "$LOG_DIR"/*/; do
            if [ -d "$dir" ]; then
                service_name=$(basename "$dir")
                echo -e "\n${YELLOW}=== $service_name ===${NC}"
                latest_log=$(find "$dir" -name "all-*.log" -type f -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-)
                if [ -n "$latest_log" ]; then
                    tail -n 20 "$latest_log"
                else
                    echo "Aucun log trouvé"
                fi
            fi
        done
    else
        if [ -d "$LOG_DIR/$service" ]; then
            echo -e "${BLUE}📋 Logs de $service${NC}"
            latest_log=$(find "$LOG_DIR/$service" -name "all-*.log" -type f -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-)
            if [ -n "$latest_log" ]; then
                cat "$latest_log"
            else
                echo "Aucun log trouvé pour $service"
            fi
        else
            echo -e "${RED}❌ Service '$service' non trouvé${NC}"
            echo "Services disponibles: $(ls -1 "$LOG_DIR" 2>/dev/null | tr '\n' ' ')"
        fi
    fi
}

tail_logs() {
    local service=${1:-"all"}
    
    if [ "$service" = "all" ]; then
        echo -e "${BLUE}👁️  Suivi de tous les logs en temps réel${NC}"
        echo -e "${YELLOW}Appuyez sur Ctrl+C pour arrêter${NC}"
        tail -f "$LOG_DIR"/*/all-*.log 2>/dev/null
    else
        if [ -d "$LOG_DIR/$service" ]; then
            echo -e "${BLUE}👁️  Suivi des logs de $service en temps réel${NC}"
            echo -e "${YELLOW}Appuyez sur Ctrl+C pour arrêter${NC}"
            tail -f "$LOG_DIR/$service"/all-*.log 2>/dev/null
        else
            echo -e "${RED}❌ Service '$service' non trouvé${NC}"
        fi
    fi
}

clean_logs() {
    local days=${1:-7}
    echo -e "${BLUE}🧹 Nettoyage des logs plus anciens que $days jours${NC}"
    
    if [ ! -d "$LOG_DIR" ]; then
        echo -e "${YELLOW}⚠️  Aucun dossier de logs trouvé${NC}"
        return
    fi
    
    # Compter les fichiers avant nettoyage
    before_count=$(find "$LOG_DIR" -name "*.log" -type f | wc -l)
    
    # Supprimer les logs anciens
    find "$LOG_DIR" -name "*.log" -type f -mtime +$days -delete
    
    # Compter les fichiers après nettoyage
    after_count=$(find "$LOG_DIR" -name "*.log" -type f | wc -l)
    deleted_count=$((before_count - after_count))
    
    echo -e "${GREEN}✅ $deleted_count fichiers de logs supprimés${NC}"
}

show_size() {
    echo -e "${BLUE}📊 Taille des logs par service${NC}"
    echo "----------------------------------------"
    
    if [ ! -d "$LOG_DIR" ]; then
        echo -e "${YELLOW}⚠️  Aucun dossier de logs trouvé${NC}"
        return
    fi
    
    total_size=0
    for dir in "$LOG_DIR"/*/; do
        if [ -d "$dir" ]; then
            service_name=$(basename "$dir")
            size=$(du -sh "$dir" 2>/dev/null | cut -f1)
            size_bytes=$(du -sb "$dir" 2>/dev/null | cut -f1)
            total_size=$((total_size + size_bytes))
            printf "%-15s: %s\n" "$service_name" "$size"
        fi
    done
    
    echo "----------------------------------------"
    total_size_human=$(echo $total_size | awk '{
        if ($1 >= 1073741824) printf "%.2f GB", $1/1073741824
        else if ($1 >= 1048576) printf "%.2f MB", $1/1048576
        else if ($1 >= 1024) printf "%.2f KB", $1/1024
        else printf "%d bytes", $1
    }')
    printf "%-15s: %s\n" "TOTAL" "$total_size_human"
}

backup_logs() {
    local backup_dir="./logs_backup"
    local backup_file="logs_backup_$DATE.tar.gz"
    
    echo -e "${BLUE}💾 Sauvegarde des logs${NC}"
    
    if [ ! -d "$LOG_DIR" ]; then
        echo -e "${YELLOW}⚠️  Aucun dossier de logs à sauvegarder${NC}"
        return
    fi
    
    mkdir -p "$backup_dir"
    tar -czf "$backup_dir/$backup_file" -C "." logs/
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Logs sauvegardés dans $backup_dir/$backup_file${NC}"
        echo "Taille: $(du -sh "$backup_dir/$backup_file" | cut -f1)"
    else
        echo -e "${RED}❌ Erreur lors de la sauvegarde${NC}"
    fi
}

rotate_logs() {
    echo -e "${BLUE}🔄 Rotation des logs${NC}"
    
    if [ ! -d "$LOG_DIR" ]; then
        echo -e "${YELLOW}⚠️  Aucun dossier de logs trouvé${NC}"
        return
    fi
    
    # Faire une sauvegarde avant la rotation
    backup_logs
    
    # Déplacer les logs actuels avec un timestamp
    for dir in "$LOG_DIR"/*/; do
        if [ -d "$dir" ]; then
            service_name=$(basename "$dir")
            for log_file in "$dir"/*.log; do
                if [ -f "$log_file" ]; then
                    filename=$(basename "$log_file")
                    mv "$log_file" "${log_file%.log}_rotated_$DATE.log"
                fi
            done
            echo -e "${GREEN}✅ Logs de $service_name pivotés${NC}"
        fi
    done
}

# Script principal
case "${1:-help}" in
    "show")
        show_logs "$2"
        ;;
    "tail")
        tail_logs "$2"
        ;;
    "clean")
        clean_logs "$2"
        ;;
    "size")
        show_size
        ;;
    "backup")
        backup_logs
        ;;
    "rotate")
        rotate_logs
        ;;
    "help"|*)
        print_usage
        ;;
esac
