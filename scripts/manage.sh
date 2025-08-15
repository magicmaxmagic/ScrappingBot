#!/bin/bash

# ScrappingBot Management Helper
# Quick access to common operations

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

show_logo() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║  🕷️  ScrappingBot Management Console  🤖                          ║"
    echo "║                                                                  ║"
    echo "║  Intelligent Real Estate Data Collection & Analysis Platform    ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

show_menu() {
    echo -e "${CYAN}Quick Actions:${NC}"
    echo "1. 🚀 Quick Start (First time setup)"
    echo "2. ▶️  Start All Services"
    echo "3. ⏹️  Stop All Services"
    echo "4. 🔄 Restart All Services"
    echo "5. 📊 System Health Check"
    echo "6. 📈 Live Monitoring Dashboard"
    echo "7. 📝 View Logs"
    echo "8. 🕷️  Run Test Scrape"
    echo "9. 🗄️  Database Operations"
    echo "10. 🤖 AI/LLM Operations"
    echo "11. 🧹 Cleanup Options"
    echo "12. ❓ Help & Documentation"
    echo "0. 🚪 Exit"
    echo ""
}

database_menu() {
    echo -e "${YELLOW}Database Operations:${NC}"
    echo "1. Initialize Database"
    echo "2. Load Montreal Areas"
    echo "3. Database Statistics"
    echo "4. Create Backup"
    echo "5. Restore Backup"
    echo "6. Database Shell"
    echo "0. Back to Main Menu"
    echo ""
}

llm_menu() {
    echo -e "${YELLOW}AI/LLM Operations:${NC}"
    echo "1. List Available Models"
    echo "2. Pull New Model"
    echo "3. Test Chat Interface"
    echo "4. Chatbot Service Logs"
    echo "0. Back to Main Menu"
    echo ""
}

cleanup_menu() {
    echo -e "${YELLOW}Cleanup Options:${NC}"
    echo "1. Clean Docker Resources"
    echo "2. Clean Old Logs"
    echo "3. 🚨 DANGER: Complete Reset (All Data Lost)"
    echo "0. Back to Main Menu"
    echo ""
}

execute_with_status() {
    local command="$1"
    local description="$2"
    
    echo -e "${BLUE}$description...${NC}"
    if eval "$command"; then
        echo -e "${GREEN}✅ Success!${NC}"
    else
        echo -e "${RED}❌ Failed!${NC}"
    fi
    echo ""
    read -p "Press Enter to continue..."
}

main_menu() {
    while true; do
        clear
        show_logo
        show_menu
        
        read -p "Choose an option (0-12): " choice
        
        case $choice in
            1)
                execute_with_status "make setup" "Setting up ScrappingBot for first time"
                ;;
            2)
                execute_with_status "make up" "Starting all services"
                ;;
            3)
                execute_with_status "make down" "Stopping all services"
                ;;
            4)
                execute_with_status "make restart" "Restarting all services"
                ;;
            5)
                clear
                echo -e "${BLUE}Running comprehensive health check...${NC}"
                ./scripts/docker/health-check.sh
                echo ""
                read -p "Press Enter to continue..."
                ;;
            6)
                clear
                echo -e "${BLUE}Starting live monitoring dashboard...${NC}"
                echo -e "${YELLOW}Press Ctrl+C to return to menu${NC}"
                echo ""
                ./scripts/docker/monitor.sh
                ;;
            7)
                clear
                echo -e "${BLUE}Viewing all service logs (Ctrl+C to stop)...${NC}"
                make logs
                ;;
            8)
                execute_with_status "make scrape-test" "Running test scrape"
                ;;
            9)
                database_submenu
                ;;
            10)
                llm_submenu
                ;;
            11)
                cleanup_submenu
                ;;
            12)
                clear
                echo -e "${CYAN}📚 Documentation & Help:${NC}"
                echo ""
                echo "📖 Main Documentation: README.md"
                echo "🔧 Troubleshooting Guide: TROUBLESHOOTING.md"
                echo "⚙️  Environment Template: .env.example"
                echo ""
                echo -e "${YELLOW}Useful Commands:${NC}"
                echo "make help              # Show all available commands"
                echo "make health-full       # Comprehensive health check"
                echo "make monitor-live      # Live monitoring dashboard"
                echo "make info             # System information"
                echo ""
                echo -e "${YELLOW}Service URLs:${NC}"
                echo "Frontend:    http://localhost:3000"
                echo "API:         http://localhost:8787"
                echo "Chatbot:     http://localhost:8080"  
                echo "Grafana:     http://localhost:3001"
                echo ""
                read -p "Press Enter to continue..."
                ;;
            0)
                echo -e "${GREEN}Thank you for using ScrappingBot! 🕷️${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid option. Please try again.${NC}"
                sleep 2
                ;;
        esac
    done
}

database_submenu() {
    while true; do
        clear
        show_logo
        database_menu
        
        read -p "Choose database operation (0-6): " db_choice
        
        case $db_choice in
            1)
                execute_with_status "make db-init" "Initializing database schema"
                ;;
            2)
                execute_with_status "make db-load-areas" "Loading Montreal area data"
                ;;
            3)
                execute_with_status "make db-stats" "Getting database statistics"
                ;;
            4)
                execute_with_status "make db-backup" "Creating database backup"
                ;;
            5)
                execute_with_status "make db-restore" "Restoring database from backup"
                ;;
            6)
                echo -e "${BLUE}Opening database shell...${NC}"
                echo -e "${YELLOW}Use \\q to exit${NC}"
                make shell-db
                ;;
            0)
                break
                ;;
            *)
                echo -e "${RED}Invalid option. Please try again.${NC}"
                sleep 2
                ;;
        esac
    done
}

llm_submenu() {
    while true; do
        clear
        show_logo
        llm_menu
        
        read -p "Choose AI/LLM operation (0-4): " llm_choice
        
        case $llm_choice in
            1)
                execute_with_status "make llm-list" "Listing available LLM models"
                ;;
            2)
                echo -e "${BLUE}Which model to pull? (default: llama3.1)${NC}"
                read -p "Model name: " model_name
                model_name=${model_name:-llama3.1}
                execute_with_status "MODEL_NAME=$model_name make llm-pull" "Pulling model $model_name"
                ;;
            3)
                echo -e "${BLUE}Starting chat interface...${NC}"
                echo -e "${YELLOW}Type /bye to exit${NC}"
                make llm-chat
                ;;
            4)
                clear
                echo -e "${BLUE}Chatbot service logs (Ctrl+C to stop)...${NC}"
                make logs-chatbot
                ;;
            0)
                break
                ;;
            *)
                echo -e "${RED}Invalid option. Please try again.${NC}"
                sleep 2
                ;;
        esac
    done
}

cleanup_submenu() {
    while true; do
        clear
        show_logo
        cleanup_menu
        
        read -p "Choose cleanup operation (0-3): " cleanup_choice
        
        case $cleanup_choice in
            1)
                execute_with_status "make clean" "Cleaning Docker resources"
                ;;
            2)
                execute_with_status "make clean-logs" "Cleaning old log files"
                ;;
            3)
                echo -e "${RED}⚠️  WARNING: This will delete ALL data including the database!${NC}"
                echo -e "${YELLOW}This action cannot be undone!${NC}"
                read -p "Are you absolutely sure? Type 'DELETE ALL DATA' to confirm: " confirm
                if [ "$confirm" = "DELETE ALL DATA" ]; then
                    execute_with_status "make clean-all" "Performing complete reset"
                else
                    echo -e "${YELLOW}Operation cancelled.${NC}"
                    sleep 2
                fi
                ;;
            0)
                break
                ;;
            *)
                echo -e "${RED}Invalid option. Please try again.${NC}"
                sleep 2
                ;;
        esac
    done
}

# Check if script is being run from correct directory
if [ ! -f "Makefile" ] || [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Please run this script from the ScrappingBot root directory${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Start main menu
main_menu
