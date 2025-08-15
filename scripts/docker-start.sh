#!/bin/bash
# Quick start script for ScrappingBot Docker

set -e

echo "🐳 ScrappingBot Docker Quick Start"
echo "=================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check requirements
print_info "Checking requirements..."

if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

print_success "Docker and Docker Compose found"

# Check if .env exists, create if not
if [ ! -f .env ]; then
    print_info "Creating .env file..."
    cat > .env << EOF
# PostgreSQL Configuration
DATABASE_URL=postgresql://scrappingbot_user:scrappingbot_pass@postgres:5432/scrappingbot

# API Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:80

# LLM Configuration
OLLAMA_MODEL=llama3.1

# Environment
NODE_ENV=production
DEBUG=0
EOF
    print_success ".env file created"
fi

# Start the application
print_info "Starting ScrappingBot with Docker..."
make setup

print_success "ScrappingBot is starting!"
echo ""
print_info "Access the application:"
echo "  🌐 Frontend:  http://localhost:3000"
echo "  🔌 API:       http://localhost:8787"  
echo "  💬 Chatbot:   http://localhost:8080"
echo "  📊 Monitoring: http://localhost:3001"
echo ""
print_info "Useful commands:"
echo "  make status    - Check service status"
echo "  make logs      - View all logs"
echo "  make health    - Check service health"
echo "  make down      - Stop all services"
echo ""
print_warning "First startup may take several minutes to download images and initialize database."

# Wait and check health
echo "Waiting 60 seconds for services to initialize..."
sleep 60

echo ""
print_info "Checking service health..."
make health
