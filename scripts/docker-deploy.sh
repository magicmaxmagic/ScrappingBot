#!/bin/bash
# ScrappingBot Docker Deployment Script
# Complete multi-container setup with monitoring

set -e

echo "🐳 ScrappingBot Docker Deployment"
echo "================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check dependencies
check_dependencies() {
    print_info "Checking dependencies..."
    
    if ! command -v docker >&2 /dev/null; then
        print_error "Docker not found. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose >&2 /dev/null && ! command -v docker compose >&2 /dev/null; then
        print_error "Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    
    print_status "Dependencies check passed"
}

# Create required directories
create_directories() {
    print_info "Creating required directories..."
    
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/data"
    mkdir -p "$PROJECT_ROOT/docker/grafana/dashboards"
    mkdir -p "$PROJECT_ROOT/docker/grafana/provisioning/dashboards"
    mkdir -p "$PROJECT_ROOT/docker/grafana/provisioning/datasources"
    
    print_status "Directories created"
}

# Generate environment files
generate_env_files() {
    print_info "Generating environment configuration..."
    
    # Main .env file
    cat > "$PROJECT_ROOT/.env" << 'EOF'
# PostgreSQL Configuration
POSTGRES_DB=scrappingbot
POSTGRES_USER=scrappingbot_user
POSTGRES_PASSWORD=scrappingbot_pass

# Database URLs
DATABASE_URL=postgresql://scrappingbot_user:scrappingbot_pass@postgres:5432/scrappingbot
REDIS_URL=redis://redis:6379

# API Configuration
VITE_API_URL=http://localhost:8787
VITE_CHATBOT_URL=http://localhost:8080
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost

# LLM Configuration
OLLAMA_HOST=ollama:11434
OLLAMA_MODEL=llama3.1

# Monitoring
GRAFANA_ADMIN_PASSWORD=admin123

# Environment
ENVIRONMENT=development
EOF

    print_status "Environment files generated"
}

# Pull Ollama models
setup_ollama() {
    print_info "Setting up Ollama LLM models..."
    
    # Start only Ollama service first
    docker compose up -d ollama
    
    # Wait for Ollama to be ready
    echo "Waiting for Ollama to start..."
    sleep 30
    
    # Pull required models
    docker compose exec ollama ollama pull llama3.1 || print_warning "Failed to pull llama3.1 model"
    docker compose exec ollama ollama pull codellama || print_warning "Failed to pull codellama model"
    
    print_status "Ollama models setup completed"
}

# Initialize database
init_database() {
    print_info "Initializing PostgreSQL database..."
    
    # Start database services
    docker compose up -d postgres redis
    
    # Wait for database to be ready
    echo "Waiting for PostgreSQL to start..."
    sleep 20
    
    # Run database initialization
    docker compose run --rm scraper python database/setup.py --init || print_warning "Database init may have failed"
    
    print_status "Database initialization completed"
}

# Load area data
load_area_data() {
    print_info "Loading Montreal area data..."
    
    # Check if GeoJSON data exists
    if [ -f "$PROJECT_ROOT/data/montreal-areas.geojson" ]; then
        docker compose run --rm scraper python database/setup.py --load-areas /app/data/montreal-areas.geojson
        print_status "Area data loaded successfully"
    else
        print_warning "No GeoJSON area data found. You can load it later with:"
        echo "docker compose run --rm scraper python database/setup.py --load-areas /app/data/your-areas.geojson"
    fi
}

# Build and start services
start_services() {
    print_info "Building and starting all services..."
    
    # Build all services
    docker compose build
    
    # Start all services
    docker compose up -d
    
    print_status "All services started"
}

# Verify deployment
verify_deployment() {
    print_info "Verifying deployment..."
    
    sleep 30  # Give services time to start
    
    # Check service health
    services=("postgres" "redis" "scraper" "chatbot" "api" "frontend" "nginx")
    
    for service in "${services[@]}"; do
        if docker compose ps $service | grep -q "Up"; then
            print_status "$service is running"
        else
            print_error "$service is not running properly"
        fi
    done
    
    # Test API endpoint
    if curl -f http://localhost/health >&2 /dev/null; then
        print_status "API health check passed"
    else
        print_warning "API health check failed - services may still be starting"
    fi
}

# Show deployment info
show_info() {
    echo ""
    print_status "🎉 ScrappingBot deployment completed!"
    echo ""
    print_info "Access your services:"
    echo "  🌐 Frontend:  http://localhost"
    echo "  📡 API:       http://localhost/api"
    echo "  💬 Chatbot:   http://localhost/chat"
    echo "  📊 Grafana:   http://localhost:3001 (admin/admin123)"
    echo "  🔧 Ollama:    http://localhost:11434"
    echo ""
    print_info "Useful commands:"
    echo "  📋 View logs:     docker compose logs -f [service]"
    echo "  🔍 Service status: docker compose ps"
    echo "  🛑 Stop all:      docker compose down"
    echo "  🗑️  Clean up:     docker compose down -v"
    echo "  🔄 Restart:       docker compose restart [service]"
    echo ""
    print_info "Services starting in background. Check logs with:"
    echo "  docker compose logs -f"
}

# Clean up existing deployment
cleanup() {
    print_info "Cleaning up existing deployment..."
    docker compose down -v 2>/dev/null || true
    docker system prune -f >/dev/null 2>&1 || true
    print_status "Cleanup completed"
}

# Main deployment process
main() {
    echo "Starting ScrappingBot Docker deployment..."
    echo "Project root: $PROJECT_ROOT"
    echo ""
    
    check_dependencies
    create_directories
    generate_env_files
    
    # Ask user about cleanup
    read -p "Clean up existing deployment? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup
    fi
    
    # Setup services step by step
    setup_ollama
    init_database
    load_area_data
    start_services
    verify_deployment
    show_info
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        echo "ScrappingBot Docker Deployment Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h       Show this help message"
        echo "  --cleanup        Clean up existing deployment and exit"
        echo "  --verify         Verify existing deployment"
        echo "  --logs           Show service logs"
        echo "  --status         Show service status"
        echo ""
        exit 0
        ;;
    --cleanup)
        cleanup
        print_status "Cleanup completed"
        exit 0
        ;;
    --verify)
        verify_deployment
        exit 0
        ;;
    --logs)
        docker compose logs -f
        exit 0
        ;;
    --status)
        docker compose ps
        exit 0
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
