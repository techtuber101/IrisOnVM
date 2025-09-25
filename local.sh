#!/bin/bash

# Local Development Deployment Script
# Uses .env.local files for development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Local Development Environment${NC}"

# Check if rebuild flag is passed
REBUILD_FLAG=""
if [[ "$1" == "rebuild" ]]; then
    REBUILD_FLAG="--no-cache"
    echo -e "${YELLOW}📦 Rebuild mode: Building with --no-cache${NC}"
fi

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker compose -f docker-compose.local.yml down

# Start containers with local environment files
echo -e "${GREEN}⚡ Starting local development environment...${NC}"
if [[ -n "$REBUILD_FLAG" ]]; then
    docker compose -f docker-compose.local.yml build --no-cache
    docker compose -f docker-compose.local.yml up -d
else
    docker compose -f docker-compose.local.yml up --build -d
fi

# Wait a moment for services to start
sleep 3

# Check if services are running
echo -e "${BLUE}🔍 Checking service status...${NC}"
docker compose -f docker-compose.local.yml ps

echo -e "${GREEN}✅ Local development environment is ready!${NC}"
echo -e "${BLUE}🌐 Frontend: http://localhost:3000${NC}"
echo -e "${BLUE}🔧 Backend API: http://localhost:8000${NC}"
echo -e "${BLUE}📊 API Health: http://localhost:8000/api/health${NC}"

echo -e "\n${YELLOW}💡 Usage:${NC}"
echo -e "  ${BLUE}./local.sh${NC}        - Start with cache"
echo -e "  ${BLUE}./local.sh rebuild${NC} - Start with --no-cache"
echo -e "  ${BLUE}docker compose logs -f${NC} - View logs"
echo -e "  ${BLUE}docker compose down${NC} - Stop services"
