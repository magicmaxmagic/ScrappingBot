#!/bin/bash

# ScrappingBot Monitoring Script
# Surveillance en temps réel des services Docker

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REFRESH_INTERVAL=5
LOG_LINES=10

# Function to clear screen
clear_screen() {
    clear
    echo -e "${BLUE}🖥️  ScrappingBot Live Monitor${NC}"
    echo "===================================="
    echo -e "${CYAN}Refresh: ${REFRESH_INTERVAL}s | $(date)${NC}"
    echo ""
}

# Function to show Docker containers status
show_containers_status() {
    echo -e "${PURPLE}📦 Containers Status${NC}"
    echo "===================="
    
    # Get container stats
    if command -v docker-compose >/dev/null 2>&1; then
        docker-compose ps --format table
    else
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    fi
    echo ""
}

# Function to show resource usage
show_resource_usage() {
    echo -e "${PURPLE}📊 Resource Usage${NC}"
    echo "=================="
    
    # Docker stats (non-blocking)
    timeout 2 docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null || echo "Docker stats unavailable"
    echo ""
}

# Function to show recent logs
show_recent_logs() {
    local service=$1
    local lines=${2:-5}
    
    echo -e "${PURPLE}📝 Recent logs for $service${NC}"
    echo "$(printf '=%.0s' {1..30})"
    
    if docker-compose logs --tail="$lines" "$service" 2>/dev/null; then
        echo ""
    else
        echo -e "${RED}No logs available for $service${NC}"
        echo ""
    fi
}

# Function to check service health
check_service_health() {
    local service=$1
    local port=$2
    
    if nc -z localhost "$port" 2>/dev/null; then
        echo -e "${GREEN}✅ $service (port $port)${NC}"
    else
        echo -e "${RED}❌ $service (port $port)${NC}"
    fi
}

# Function to show network status
show_network_status() {
    echo -e "${PURPLE}🌐 Network Status${NC}"
    echo "=================="
    
    check_service_health "PostgreSQL" "5432"
    check_service_health "Redis" "6379"
    check_service_health "API" "8787"
    check_service_health "ETL" "8788"
    check_service_health "Frontend" "3000"
    check_service_health "Chatbot" "8080"
    
    echo ""
}

# Function to show disk usage
show_disk_usage() {
    echo -e "${PURPLE}💾 Docker Disk Usage${NC}"
    echo "===================="
    
    if command -v docker >/dev/null 2>&1; then
        docker system df 2>/dev/null || echo "Docker disk info unavailable"
    else
        echo "Docker not available"
    fi
    echo ""
}

# Function to show application metrics
show_app_metrics() {
    echo -e "${PURPLE}📈 Application Metrics${NC}"
    echo "======================"
    
    # ETL Status
    if docker-compose exec -T etl python -c "
import redis
r = redis.Redis(host='redis', port=6379, db=0)
try:
    keys = r.keys('*')
    print(f'Redis keys: {len(keys)}')
except:
    print('Redis connection failed')
" 2>/dev/null; then
        echo ""
    else
        echo "ETL metrics unavailable"
    fi
    
    # Database status
    if docker-compose exec -T postgres psql -U scrappingbot_user -d scrappingbot -c "
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables 
ORDER BY n_tup_ins DESC 
LIMIT 5;
" 2>/dev/null; then
        echo ""
    else
        echo "Database metrics unavailable"
        echo ""
    fi
}

# Main monitoring loop
main_loop() {
    local show_logs=${1:-false}
    local log_service=${2:-etl}
    
    while true; do
        clear_screen
        
        # Show basic container status
        show_containers_status
        
        # Show network connectivity
        show_network_status
        
        # Show resource usage
        show_resource_usage
        
        # Show disk usage
        show_disk_usage
        
        # Show application metrics
        show_app_metrics
        
        # Show logs if requested
        if [ "$show_logs" = "true" ]; then
            show_recent_logs "$log_service" "$LOG_LINES"
        fi
        
        echo -e "${CYAN}Press Ctrl+C to exit | Next refresh in ${REFRESH_INTERVAL}s${NC}"
        
        # Wait for next refresh or user input
        sleep "$REFRESH_INTERVAL"
    done
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -i, --interval SECONDS  Refresh interval (default: 5)"
    echo "  -l, --logs SERVICE      Show logs for specific service"
    echo "  -n, --lines NUMBER      Number of log lines to show (default: 10)"
    echo ""
    echo "Services: postgres, redis, etl, api, scraper, chatbot, frontend"
    echo ""
    echo "Examples:"
    echo "  $0                      # Basic monitoring"
    echo "  $0 -l etl              # Monitor with ETL logs"
    echo "  $0 -i 10 -l api -n 20  # 10s interval, API logs, 20 lines"
}

# Parse command line arguments
SHOW_LOGS=false
LOG_SERVICE="etl"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -i|--interval)
            REFRESH_INTERVAL="$2"
            shift 2
            ;;
        -l|--logs)
            SHOW_LOGS=true
            LOG_SERVICE="$2"
            shift 2
            ;;
        -n|--lines)
            LOG_LINES="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate inputs
if ! [[ "$REFRESH_INTERVAL" =~ ^[0-9]+$ ]] || [ "$REFRESH_INTERVAL" -lt 1 ]; then
    echo "Error: Refresh interval must be a positive integer"
    exit 1
fi

if ! [[ "$LOG_LINES" =~ ^[0-9]+$ ]] || [ "$LOG_LINES" -lt 1 ]; then
    echo "Error: Log lines must be a positive integer"
    exit 1
fi

# Check if Docker is available
if ! command -v docker >/dev/null 2>&1; then
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1; then
    echo "Error: docker-compose is not installed or not in PATH"
    exit 1
fi

# Trap Ctrl+C for clean exit
trap 'echo -e "\n${GREEN}Monitoring stopped${NC}"; exit 0' INT

echo -e "${GREEN}Starting ScrappingBot monitoring...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
sleep 2

# Start monitoring
main_loop "$SHOW_LOGS" "$LOG_SERVICE"
