#!/bin/bash
# PostgreSQL + PostGIS Setup for ScrappingBot
# Automated installation and configuration script

set -e

echo "🚀 ScrappingBot PostgreSQL Setup"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATABASE_DIR="$PROJECT_ROOT/database"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install PostgreSQL dependencies
install_python_deps() {
    print_info "Installing Python dependencies..."
    
    if [ -f "$DATABASE_DIR/requirements.txt" ]; then
        pip install -r "$DATABASE_DIR/requirements.txt"
        print_status "Python dependencies installed"
    else
        print_warning "Database requirements.txt not found, installing manually"
        pip install asyncpg psycopg2-binary
    fi
}

# Check PostgreSQL installation
check_postgresql() {
    print_info "Checking PostgreSQL installation..."
    
    if command_exists psql; then
        POSTGRES_VERSION=$(psql --version | grep -oP '\d+\.\d+' | head -1)
        print_status "PostgreSQL $POSTGRES_VERSION found"
        return 0
    else
        print_warning "PostgreSQL not found in PATH"
        return 1
    fi
}

# Install PostgreSQL (macOS)
install_postgresql_macos() {
    print_info "Installing PostgreSQL on macOS..."
    
    if command_exists brew; then
        brew install postgresql@15 postgis
        brew services start postgresql@15
        print_status "PostgreSQL installed and started"
    else
        print_error "Homebrew not found. Please install PostgreSQL manually:"
        echo "1. Install Homebrew: https://brew.sh"
        echo "2. Run: brew install postgresql@15 postgis"
        exit 1
    fi
}

# Install PostgreSQL (Ubuntu/Debian)
install_postgresql_ubuntu() {
    print_info "Installing PostgreSQL on Ubuntu/Debian..."
    
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib postgis postgresql-15-postgis-3
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    print_status "PostgreSQL installed and started"
}

# Setup PostgreSQL database
setup_database() {
    print_info "Setting up ScrappingBot database..."
    
    DB_NAME="scrappingbot"
    DB_USER="scrappingbot_user"
    DB_PASS="scrappingbot_pass"
    
    # Create database and user
    sudo -u postgres psql << EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER USER $DB_USER CREATEDB;
\q
EOF

    # Enable PostGIS extension
    sudo -u postgres psql -d "$DB_NAME" << EOF
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
\q
EOF

    print_status "Database '$DB_NAME' created with PostGIS extension"
    
    # Create .env file
    cat > "$PROJECT_ROOT/.env" << EOF
# PostgreSQL Configuration for ScrappingBot
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME

# API Configuration  
VITE_API_URL=http://localhost:8787
CORS_ORIGIN=http://localhost:5173

# Optional: Supabase configuration
# DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
EOF

    print_status "Environment configuration created (.env)"
}

# Run database schema migration
run_schema_migration() {
    print_info "Running database schema migration..."
    
    if [ -f "$DATABASE_DIR/setup.py" ]; then
        cd "$PROJECT_ROOT"
        python "$DATABASE_DIR/setup.py" --init
        print_status "Schema migration completed"
    else
        print_error "Database setup script not found"
        exit 1
    fi
}

# Load Montreal area data
load_area_data() {
    print_info "Loading Montreal area data..."
    
    # Look for GeoJSON files
    GEOJSON_FILE=""
    for file in "$PROJECT_ROOT/data"/*.geojson "$PROJECT_ROOT/data"/*.json; do
        if [ -f "$file" ] && grep -q "Feature" "$file" 2>/dev/null; then
            GEOJSON_FILE="$file"
            break
        fi
    done
    
    if [ -n "$GEOJSON_FILE" ]; then
        python "$DATABASE_DIR/setup.py" --load-areas "$GEOJSON_FILE"
        print_status "Area data loaded from $(basename "$GEOJSON_FILE")"
    else
        print_warning "No GeoJSON area data found in data/ directory"
        print_info "You can load area data later with:"
        echo "python database/setup.py --load-areas path/to/areas.geojson"
    fi
}

# Install Node.js dependencies for Workers
setup_workers() {
    print_info "Setting up Cloudflare Workers API..."
    
    WORKERS_DIR="$PROJECT_ROOT/workers/postgres-api"
    
    if [ -d "$WORKERS_DIR" ] && [ -f "$WORKERS_DIR/package.json" ]; then
        cd "$WORKERS_DIR"
        
        if command_exists npm; then
            npm install
            print_status "Worker dependencies installed"
            
            print_info "To start the API worker:"
            echo "cd workers/postgres-api && npm run dev"
        else
            print_warning "npm not found - please install Node.js"
        fi
    else
        print_warning "Workers directory not found or incomplete"
    fi
}

# Setup frontend
setup_frontend() {
    print_info "Setting up React frontend..."
    
    FRONTEND_DIR="$PROJECT_ROOT/frontend"
    
    if [ -d "$FRONTEND_DIR" ] && [ -f "$FRONTEND_DIR/package.json" ]; then
        cd "$FRONTEND_DIR"
        
        if command_exists npm; then
            npm install
            print_status "Frontend dependencies installed"
            
            print_info "To start the frontend:"
            echo "cd frontend && npm run dev"
        else
            print_warning "npm not found - please install Node.js"
        fi
    else
        print_warning "Frontend directory not found or incomplete"
    fi
}

# Verify installation
verify_installation() {
    print_info "Verifying installation..."
    
    cd "$PROJECT_ROOT"
    
    if python "$DATABASE_DIR/setup.py" --verify; then
        print_status "Installation verification passed"
        return 0
    else
        print_error "Installation verification failed"
        return 1
    fi
}

# Main installation process
main() {
    echo "Starting ScrappingBot PostgreSQL setup..."
    echo "Project root: $PROJECT_ROOT"
    echo ""
    
    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt; then
            OS="ubuntu"
        else
            OS="linux"
        fi
    else
        OS="unknown"
    fi
    
    print_info "Detected OS: $OS"
    
    # Install Python dependencies first
    install_python_deps
    
    # Check if PostgreSQL is already installed
    if ! check_postgresql; then
        print_warning "PostgreSQL not found, attempting installation..."
        
        case $OS in
            macos)
                install_postgresql_macos
                ;;
            ubuntu)
                install_postgresql_ubuntu
                ;;
            *)
                print_error "Automated PostgreSQL installation not supported for $OS"
                print_info "Please install PostgreSQL 12+ with PostGIS extension manually"
                exit 1
                ;;
        esac
    fi
    
    # Setup database
    setup_database
    
    # Run schema migration
    run_schema_migration
    
    # Load area data
    load_area_data
    
    # Setup Workers and Frontend
    setup_workers
    setup_frontend
    
    # Verify installation
    if verify_installation; then
        echo ""
        print_status "🎉 Installation completed successfully!"
        echo ""
        print_info "Next steps:"
        echo "1. Test the enhanced scraper:"
        echo "   python database/scraper_adapter.py --where Montreal --what condo"
        echo ""
        echo "2. Start the API worker (in a new terminal):"
        echo "   cd workers/postgres-api && npm run dev"
        echo ""
        echo "3. Start the frontend (in a new terminal):"
        echo "   cd frontend && npm run dev"
        echo ""
        echo "4. Open http://localhost:5173 in your browser"
        echo ""
        print_info "Database connection: $(grep DATABASE_URL .env)"
    else
        print_error "Installation completed with errors - please check the logs above"
        exit 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            echo "ScrappingBot PostgreSQL Setup Script"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --help, -h          Show this help message"
            echo "  --deps-only         Install Python dependencies only"
            echo "  --verify-only       Run verification only"
            echo ""
            exit 0
            ;;
        --deps-only)
            install_python_deps
            exit 0
            ;;
        --verify-only)
            verify_installation
            exit $?
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
    shift
done

# Run main installation if no specific options
main
