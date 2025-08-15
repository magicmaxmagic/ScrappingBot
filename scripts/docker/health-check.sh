#!/bin/bash

# ScrappingBot Health Check Script
# Comprehensive health monitoring for all services

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏥 ScrappingBot Health Check${NC}"
echo "================================"
echo ""

# Function to check service health
check_service() {
    local service_name="$1"
    local url="$2"
    local expected_code="${3:-200}"
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_code"; then
        echo -e "${GREEN}✅ $service_name: Healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name: Unhealthy${NC}"
        return 1
    fi
}

# Function to check container status
check_container() {
    local container_name="$1"
    
    if docker ps --filter "name=$container_name" --filter "status=running" | grep -q "$container_name"; then
        echo -e "${GREEN}✅ $container_name: Running${NC}"
        return 0
    else
        echo -e "${RED}❌ $container_name: Not Running${NC}"
        return 1
    fi
}

health_issues=0

echo -e "${YELLOW}📊 Container Status:${NC}"
containers=("scrappingbot-postgres" "scrappingbot-redis" "scrappingbot-api" "scrappingbot-scraper" "scrappingbot-chatbot" "scrappingbot-frontend" "scrappingbot-ollama" "scrappingbot-nginx" "scrappingbot-scheduler" "scrappingbot-grafana")

for container in "${containers[@]}"; do
    check_container "$container" || ((health_issues++))
done

echo ""
echo -e "${YELLOW}🌐 Service Health:${NC}"
check_service "API" "http://localhost:8787/health" || ((health_issues++))
check_service "Chatbot" "http://localhost:8080/health" || ((health_issues++))
check_service "Frontend" "http://localhost:3000" || ((health_issues++))
check_service "Grafana" "http://localhost:3001/api/health" || ((health_issues++))

echo ""
echo -e "${YELLOW}🗄️  Database Health:${NC}"
if docker exec scrappingbot-postgres pg_isready -U scrappingbot_user -d scrappingbot >/dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL: Ready${NC}"
else
    echo -e "${RED}❌ PostgreSQL: Not Ready${NC}"
    ((health_issues++))
fi

if docker exec scrappingbot-redis redis-cli ping >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis: Responding${NC}"
else
    echo -e "${RED}❌ Redis: Not Responding${NC}"
    ((health_issues++))
fi

echo ""
echo -e "${YELLOW}🤖 AI Services:${NC}"
if docker exec scrappingbot-ollama ollama list >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama: Available${NC}"
    echo "   Models: $(docker exec scrappingbot-ollama ollama list | tail -n +2 | wc -l | tr -d ' ') installed"
else
    echo -e "${RED}❌ Ollama: Not Available${NC}"
    ((health_issues++))
fi

echo ""
echo -e "${YELLOW}📈 Resource Usage:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | head -11

echo ""
if [ $health_issues -eq 0 ]; then
    echo -e "${GREEN}🎉 All systems healthy! (0 issues)${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Found $health_issues health issues${NC}"
    echo ""
    echo -e "${YELLOW}💡 Troubleshooting tips:${NC}"
    echo "  • Check logs: make logs"
    echo "  • Restart services: make restart"
    echo "  • Full rebuild: make clean && make setup"
    exit 1
fi
