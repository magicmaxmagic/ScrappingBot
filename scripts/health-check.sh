#!/bin/bash

# ScrappingBot Health Check Script
# Vérifie l'état de tous les services de l'application

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Icons
CHECKMARK="✅"
WARNING="⚠️"
ERROR="❌"
INFO="ℹ️"

echo -e "${BLUE}🏥 ScrappingBot Health Check${NC}"
echo "=================================="
echo ""

# Function to check if a port is accessible
check_port() {
    local host=$1
    local port=$2
    local service=$3
    
    if nc -z "$host" "$port" 2>/dev/null; then
        echo -e "${CHECKMARK} ${GREEN}$service${NC} - Port $port accessible"
        return 0
    else
        echo -e "${ERROR} ${RED}$service${NC} - Port $port non accessible"
        return 1
    fi
}

# Function to check HTTP endpoint
check_http() {
    local url=$1
    local service=$2
    local expected_code=${3:-200}
    
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response_code" = "$expected_code" ]; then
        echo -e "${CHECKMARK} ${GREEN}$service${NC} - HTTP $expected_code OK"
        return 0
    else
        echo -e "${ERROR} ${RED}$service${NC} - HTTP $response_code (attendu: $expected_code)"
        return 1
    fi
}

# Function to check Docker service
check_docker_service() {
    local service=$1
    
    if docker-compose ps "$service" | grep -q "Up"; then
        if docker-compose ps "$service" | grep -q "healthy"; then
            echo -e "${CHECKMARK} ${GREEN}$service${NC} - Container healthy"
            return 0
        else
            echo -e "${WARNING} ${YELLOW}$service${NC} - Container up but not healthy"
            return 1
        fi
    else
        echo -e "${ERROR} ${RED}$service${NC} - Container not running"
        return 1
    fi
}

# Function to check database connection
check_database() {
    if docker-compose exec -T postgres pg_isready -U scrappingbot_user -d scrappingbot >/dev/null 2>&1; then
        echo -e "${CHECKMARK} ${GREEN}PostgreSQL${NC} - Database ready"
        return 0
    else
        echo -e "${ERROR} ${RED}PostgreSQL${NC} - Database not ready"
        return 1
    fi
}

# Function to check Redis
check_redis() {
    if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
        echo -e "${CHECKMARK} ${GREEN}Redis${NC} - Cache ready"
        return 0
    else
        echo -e "${ERROR} ${RED}Redis${NC} - Cache not ready"
        return 1
    fi
}

# Function to test ETL functionality
check_etl_functionality() {
    if docker-compose exec -T etl python -c "
import etl.normalize
import etl.dedupe
import etl.schema
print('ETL modules imported successfully')
" >/dev/null 2>&1; then
        echo -e "${CHECKMARK} ${GREEN}ETL${NC} - Modules functional"
        return 0
    else
        echo -e "${ERROR} ${RED}ETL${NC} - Modules not functional"
        return 1
    fi
}

# Initialize counters
total_checks=0
passed_checks=0
failed_checks=0

# Helper function to run check
run_check() {
    local check_name=$1
    shift
    echo -n "Checking $check_name... "
    total_checks=$((total_checks + 1))
    if "$@"; then
        passed_checks=$((passed_checks + 1))
    else
        failed_checks=$((failed_checks + 1))
    fi
}

echo -e "${BLUE}🐳 Docker Services${NC}"
echo "==================="

# Check Docker services
services=("postgres" "redis" "etl" "api" "scraper" "chatbot" "frontend")
for service in "${services[@]}"; do
    if docker-compose ps "$service" | grep -q "$service"; then
        run_check "$service container" check_docker_service "$service"
    else
        echo -e "${INFO} ${YELLOW}$service${NC} - Service not defined in docker-compose"
    fi
done

echo ""
echo -e "${BLUE}🔌 Network Connectivity${NC}"
echo "======================="

# Check network ports
run_check "PostgreSQL port" check_port "localhost" "5432" "PostgreSQL"
run_check "Redis port" check_port "localhost" "6379" "Redis"
run_check "API port" check_port "localhost" "8787" "API"
run_check "ETL port" check_port "localhost" "8788" "ETL"
run_check "Frontend port" check_port "localhost" "3000" "Frontend"

echo ""
echo -e "${BLUE}🌐 HTTP Endpoints${NC}"
echo "=================="

# Check HTTP endpoints
run_check "API health" check_http "http://localhost:8787/health" "API"
run_check "ETL health" check_http "http://localhost:8788/health" "ETL"
run_check "Frontend" check_http "http://localhost:3000" "Frontend"

echo ""
echo -e "${BLUE}🔧 Service Functionality${NC}"
echo "========================="

# Check service functionality
run_check "Database connection" check_database
run_check "Redis connection" check_redis
run_check "ETL functionality" check_etl_functionality

echo ""
echo -e "${BLUE}📊 Health Summary${NC}"
echo "=================="

echo -e "Total checks: $total_checks"
echo -e "${GREEN}Passed: $passed_checks${NC}"
echo -e "${RED}Failed: $failed_checks${NC}"

# Calculate percentage
if [ $total_checks -gt 0 ]; then
    percentage=$((passed_checks * 100 / total_checks))
    echo -e "Success rate: $percentage%"
    
    if [ $percentage -ge 90 ]; then
        echo -e "${CHECKMARK} ${GREEN}System health: EXCELLENT${NC}"
        exit 0
    elif [ $percentage -ge 70 ]; then
        echo -e "${WARNING} ${YELLOW}System health: GOOD${NC}"
        exit 0
    elif [ $percentage -ge 50 ]; then
        echo -e "${WARNING} ${YELLOW}System health: DEGRADED${NC}"
        exit 1
    else
        echo -e "${ERROR} ${RED}System health: CRITICAL${NC}"
        exit 1
    fi
else
    echo -e "${ERROR} ${RED}No checks performed${NC}"
    exit 1
fi
