#!/bin/bash

# Production Deployment Script
# Uses production environment files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Production Environment${NC}"

# Check if rebuild flag is passed
REBUILD_FLAG=""
if [[ "$1" == "rebuild" ]]; then
    REBUILD_FLAG="--no-cache"
    echo -e "${YELLOW}📦 Rebuild mode: Building with --no-cache${NC}"
fi

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker compose -f docker-compose.production.yml down

# Start containers with production environment files
echo -e "${GREEN}⚡ Starting production environment...${NC}"
if [[ -n "$REBUILD_FLAG" ]]; then
    docker compose -f docker-compose.production.yml build --no-cache
    docker compose -f docker-compose.production.yml up -d
else
    docker compose -f docker-compose.production.yml up --build -d
fi

# Wait a moment for services to start
sleep 5

# Check if services are running
echo -e "${BLUE}🔍 Checking service status...${NC}"
docker compose -f docker-compose.production.yml ps

# Health check
echo -e "${BLUE}🏥 Performing health check...${NC}"
sleep 10
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend health check passed${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
fi

echo -e "${GREEN}✅ Production environment is ready!${NC}"
echo -e "${BLUE}🌐 Application: https://irisvision.ai${NC}"
echo -e "${BLUE}🔧 Backend API: https://irisvision.ai/api${NC}"
echo -e "${BLUE}📊 API Health: https://irisvision.ai/api/health${NC}"

echo -e "\n${YELLOW}💡 Usage:${NC}"
echo -e "  ${BLUE}./production.sh${NC}        - Start with cache"
echo -e "  ${BLUE}./production.sh rebuild${NC} - Start with --no-cache"
echo -e "  ${BLUE}docker compose logs -f${NC} - View logs"
echo -e "  ${BLUE}docker compose down${NC} - Stop services"

echo -e "\n${YELLOW}📋 Production Environment Files Used:${NC}"
echo -e "  ${BLUE}Backend:${NC} .env (production config)"
echo -e "  ${BLUE}Frontend:${NC} .env.production (production config)"
