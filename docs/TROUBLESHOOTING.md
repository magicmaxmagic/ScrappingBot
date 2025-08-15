# 🔧 ScrappingBot Troubleshooting Guide

## Quick Diagnostics

```bash
# Check overall system health
make health-full

# View real-time monitoring
make monitor-live

# Check container status
make status

# View all logs
make logs
```

## Common Issues & Solutions

### 🐳 Docker Issues

**Problem:** Containers not starting

```bash
# Solution: Clean rebuild
make clean
make build
make up
```

**Problem:** Port conflicts

```bash
# Check what's using ports
lsof -i :3000,8787,8080,3001
# Kill conflicting processes
sudo kill -9 <PID>
```

**Problem:** ARM64 vs AMD64 architecture issues

```bash
# Verify platform settings are removed from Dockerfiles
grep -r "platform.*amd64" docker/
# Should return no results after fix
```

### 🗄️ Database Issues

**Problem:** Database connection errors

```bash
# Check PostgreSQL status
make shell-db
# If fails, restart database
docker-compose restart postgres
```

**Problem:** Database not initialized

```bash
# Initialize database schema
make db-init
# Load Montreal areas
make db-load-areas
```

**Problem:** Database corruption

```bash
# Restore from backup
make db-restore
# Or full reset (WARNING: loses data)
docker-compose down -v
make setup
```

### 🕷️ Scraping Issues

**Problem:** Playwright browsers not working

```bash
# Check browser installation
make shell-scraper
playwright install --help
```

**Problem:** Scraper crashes on ARM64

```bash
# Verify ARM64 browsers are installed
docker exec scrappingbot-scraper ls -la /ms-playwright/
# Should show chromium-linux-arm64, firefox-ubuntu-20.04-arm64
```

### 🤖 AI/LLM Issues

**Problem:** Ollama models not responding

```bash
# Check model availability
make llm-list
# Pull default model
make llm-pull
# Test chat
make llm-chat
```

**Problem:** Chatbot service down

```bash
# Check chatbot logs
make logs-chatbot
# Restart chatbot
docker-compose restart chatbot
```

### 🌐 Frontend Issues

**Problem:** Frontend not loading

```bash
# Check frontend status
curl http://localhost:3000
# Restart frontend
docker-compose restart frontend
```

**Problem:** API connection errors

```bash
# Verify API health
curl http://localhost:8787/health
# Check API logs
make logs-api
```

### ⚡ Performance Issues

**Problem:** High CPU usage

```bash
# Monitor resource usage
make monitor
# Check individual container stats
docker stats scrappingbot-scraper
```

**Problem:** Memory issues

```bash
# Check memory usage per container
docker stats --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"
# Restart heavy containers
docker-compose restart scraper
```

### 🔧 Development Issues

**Problem:** Hot reload not working

```bash
# Use development mode
make dev
# Or restart in dev mode
make up-dev
```

**Problem:** Code changes not reflected

```bash
# Rebuild specific service
docker-compose build api
docker-compose up -d api
```

## Health Check Commands

### System Overview

```bash
make health-full    # Comprehensive health check
make status        # Container status
make info          # System information
```

### Service-Specific

```bash
make logs-api      # API service logs
make logs-scraper  # Scraper service logs
make logs-chatbot  # Chatbot service logs
make logs-db       # Database logs
```

### Database Management

```bash
make db-stats      # Database statistics
make db-backup     # Create backup
make db-restore    # Restore from backup
```

## Environment Variables

Check your `.env` file has all required variables:

```bash
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=scrappingbot
DB_USER=scrappingbot_user
DB_PASSWORD=scrappingbot_password

# API
API_HOST=0.0.0.0
API_PORT=8787

# Chatbot
CHATBOT_HOST=0.0.0.0
CHATBOT_PORT=8080
```

## Log Locations

### Container Logs

```bash
# View live logs
docker logs -f scrappingbot-api
docker logs -f scrappingbot-scraper
docker logs -f scrappingbot-chatbot
```

### Application Logs

```bash
# Inside containers
/app/logs/api.log
/app/logs/scraper.log
/app/logs/chatbot.log
```

## Emergency Recovery

### Complete Reset

```bash
# WARNING: This will delete ALL data
make clean-all
make setup
```

### Partial Recovery

```bash
# Just restart services
make restart

# Rebuild without data loss
make build
make restart
```

### Backup Before Changes

```bash
# Always backup before major changes
make db-backup
# Creates backup in backups/ directory
```

## Performance Tuning

### Resource Limits

Edit `docker-compose.yml` to adjust:

```yaml
services:
  scraper:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

### Scaling Services

```bash
# Scale scraper instances
docker-compose up -d --scale scraper=3

# Or use Makefile
make scale-scraper N=3
```

## Getting Help

1. Check this troubleshooting guide
2. Review container logs: `make logs`
3. Run health check: `make health-full`
4. Check system resources: `make monitor-live`
5. Review documentation: `README.md`

## Useful Docker Commands

```bash
# Remove unused images/containers
docker system prune

# View detailed container info
docker inspect scrappingbot-api

# Execute command in container
docker exec scrappingbot-api python --version

# Copy files from/to container
docker cp file.txt scrappingbot-api:/app/

# View container resource usage
docker stats --no-stream
```
