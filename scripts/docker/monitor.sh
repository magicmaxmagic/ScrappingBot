#!/bin/bash

# ScrappingBot Real-time Monitoring Dashboard
# Live monitoring with automatic refresh

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Function to clear screen and show header
show_header() {
    clear
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                  📊 ScrappingBot Monitor                     ║${NC}"
    echo -e "${BLUE}║                    $(date '+%Y-%m-%d %H:%M:%S')                        ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Function to get container status with color coding
get_container_status() {
    local container="$1"
    if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
        echo -e "${GREEN}●${NC}"
    else
        echo -e "${RED}●${NC}"
    fi
}

# Function to get service response
get_service_response() {
    local url="$1"
    local timeout="${2:-2}"
    
    local response_code
    response_code=$(curl -s -m "$timeout" -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [[ "$response_code" =~ ^2[0-9][0-9]$ ]]; then
        echo -e "${GREEN}$response_code${NC}"
    elif [[ "$response_code" =~ ^[45][0-9][0-9]$ ]]; then
        echo -e "${RED}$response_code${NC}"
    else
        echo -e "${YELLOW}---${NC}"
    fi
}

# Main monitoring loop
monitor() {
    while true; do
        show_header
        
        # Container Status
        echo -e "${CYAN}📦 Container Status:${NC}"
        printf "%-20s %s\n" "PostgreSQL" "$(get_container_status scrappingbot-postgres)"
        printf "%-20s %s\n" "Redis" "$(get_container_status scrappingbot-redis)"
        printf "%-20s %s\n" "API" "$(get_container_status scrappingbot-api)"
        printf "%-20s %s\n" "Scraper" "$(get_container_status scrappingbot-scraper)"
        printf "%-20s %s\n" "Chatbot" "$(get_container_status scrappingbot-chatbot)"
        printf "%-20s %s\n" "Frontend" "$(get_container_status scrappingbot-frontend)"
        printf "%-20s %s\n" "Ollama" "$(get_container_status scrappingbot-ollama)"
        printf "%-20s %s\n" "Nginx" "$(get_container_status scrappingbot-nginx)"
        printf "%-20s %s\n" "Scheduler" "$(get_container_status scrappingbot-scheduler)"
        printf "%-20s %s\n" "Grafana" "$(get_container_status scrappingbot-grafana)"
        
        echo ""
        
        # Service Health
        echo -e "${CYAN}🌐 Service Health:${NC}"
        printf "%-20s %s\n" "API" "$(get_service_response http://localhost:8787/health)"
        printf "%-20s %s\n" "Chatbot" "$(get_service_response http://localhost:8080/health)"  
        printf "%-20s %s\n" "Frontend" "$(get_service_response http://localhost:3000)"
        printf "%-20s %s\n" "Grafana" "$(get_service_response http://localhost:3001/api/health)"
        
        echo ""
        
        # Database Status
        echo -e "${CYAN}🗄️  Database Status:${NC}"
        if docker exec scrappingbot-postgres pg_isready -U scrappingbot_user -d scrappingbot >/dev/null 2>&1; then
            echo -e "PostgreSQL: ${GREEN}Ready${NC}"
        else
            echo -e "PostgreSQL: ${RED}Not Ready${NC}"
        fi
        
        if docker exec scrappingbot-redis redis-cli ping >/dev/null 2>&1; then
            echo -e "Redis: ${GREEN}Connected${NC}"
        else
            echo -e "Redis: ${RED}Disconnected${NC}"
        fi
        
        echo ""
        
        # Resource Usage (top 5 by CPU)
        echo -e "${CYAN}⚡ Resource Usage (Top 5):${NC}"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | \
        grep scrappingbot | \
        head -6 | \
        while IFS=$'\t' read -r name cpu mem net; do
            printf "%-20s CPU: %-8s MEM: %-15s NET: %s\n" "${name#scrappingbot-}" "$cpu" "$mem" "$net"
        done
        
        echo ""
        
        # Recent Log Activity
        echo -e "${CYAN}📝 Recent Activity (last 3 lines):${NC}"
        if docker logs scrappingbot-api --tail 1 2>/dev/null | head -1; then
            echo -e "${PURPLE}API:${NC} $(docker logs scrappingbot-api --tail 1 2>/dev/null | head -1 | cut -c1-60)..."
        fi
        if docker logs scrappingbot-scraper --tail 1 2>/dev/null | head -1; then
            echo -e "${PURPLE}Scraper:${NC} $(docker logs scrappingbot-scraper --tail 1 2>/dev/null | head -1 | cut -c1-60)..."
        fi
        
        echo ""
        echo -e "${YELLOW}Press Ctrl+C to exit • Refreshing every 5 seconds${NC}"
        echo "────────────────────────────────────────────────────────────────"
        
        sleep 5
    done
}

# Trap Ctrl+C to clean exit
trap 'echo -e "\n${GREEN}Monitoring stopped${NC}"; exit 0' INT

# Check if script is being run from correct directory
if [ ! -f "Makefile" ] || [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Please run this script from the ScrappingBot root directory${NC}"
    echo "Current directory: $(pwd)"
    echo "Expected files: Makefile, docker-compose.yml"
    exit 1
fi

# Start monitoring
monitor
