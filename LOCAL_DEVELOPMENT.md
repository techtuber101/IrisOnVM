# Local Development Setup Guide

This guide will help you set up Iris for local development on your machine.

## Prerequisites

- Docker and Docker Compose installed and running
- Python 3.11+ (managed by `mise` if available)
- Node.js 20+ (managed by `mise` if available)
- Required API keys and service credentials

## Quick Start

1. **Copy environment files:**
   ```bash
   cp backend/.env.local.example backend/.env.local
   cp frontend/.env.local.example frontend/.env.local
   ```

2. **Configure your environment:**
   Edit `backend/.env.local` and `frontend/.env.local` with your actual values:
   - Supabase credentials
   - API keys (OpenAI, Anthropic, etc.)
   - Other required services

3. **Start the development environment:**
   ```bash
   ./start-local.py
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api
   - Health check: http://localhost/health

## Development Commands

### Using the start script:
```bash
./start-local.py start    # Start all services
./start-local.py stop     # Stop all services
./start-local.py restart  # Restart all services
./start-local.py logs     # Show logs from all services
./start-local.py setup    # Show setup instructions
```

### Manual Docker Compose commands:
```bash
# Start all services
docker compose -f docker-compose.local.yml up -d

# Stop all services
docker compose -f docker-compose.local.yml down

# View logs
docker compose -f docker-compose.local.yml logs -f

# View logs for specific service
docker compose -f docker-compose.local.yml logs -f backend
```

## Architecture Overview

The local development setup uses:

- **Caddy** (port 80/443) - Reverse proxy routing localhost to services
- **Frontend** (port 3000) - Next.js development server
- **Backend** (port 8000) - FastAPI development server
- **Worker** - Background task processor
- **Redis** (port 6379) - Caching and task queue

## Environment Configuration

### Backend (.env.local)
Key variables to configure:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `OPENAI_API_KEY` - OpenAI API key
- `TAVILY_API_KEY` - Tavily search API key
- `FIRECRAWL_API_KEY` - Firecrawl web scraping API key
- `DAYTONA_API_KEY` - Daytona sandbox API key

### Frontend (.env.local)
Key variables to configure:
- `NEXT_PUBLIC_SUPABASE_URL` - Your Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key
- `NEXT_PUBLIC_BACKEND_URL` - Backend API URL (http://localhost:8000/api)

## Development Workflow

### Frontend Development
- The frontend runs in development mode with hot reloading
- Source code is mounted into the container for live updates
- Access at http://localhost:3000

### Backend Development
- The backend runs with source code mounted for live updates
- API documentation available at http://localhost:8000/docs
- Health check at http://localhost:8000/api/health

### Database Development
- Uses Supabase (cloud or local instance)
- Migrations are in `backend/supabase/migrations/`
- Run migrations with Supabase CLI

## Troubleshooting

### Common Issues

1. **Port conflicts:**
   - Ensure ports 80, 443, 3000, 8000, and 6379 are available
   - Stop other services using these ports

2. **Docker issues:**
   - Ensure Docker is running
   - Check Docker Compose version compatibility

3. **Environment variables:**
   - Verify all required environment variables are set
   - Check for typos in API keys

4. **Service startup order:**
   - Redis starts first (health check required)
   - Backend and Worker start after Redis
   - Frontend starts after Backend
   - Caddy starts last

### Debugging

1. **Check service status:**
   ```bash
   docker compose -f docker-compose.local.yml ps
   ```

2. **View service logs:**
   ```bash
   docker compose -f docker-compose.local.yml logs [service-name]
   ```

3. **Restart specific service:**
   ```bash
   docker compose -f docker-compose.local.yml restart [service-name]
   ```

## Production vs Local Development

### Key Differences

| Aspect | Production | Local Development |
|--------|------------|-------------------|
| Domain | irisvision.ai | localhost |
| SSL | HTTPS with Caddy | HTTP (Caddy handles SSL) |
| Environment | production | local |
| Logging | JSON format | Console format |
| CORS | Restricted | Permissive for localhost |
| Source Code | Built into images | Mounted volumes |

### Switching Between Environments

- **Production:** Use `docker-compose.yaml` and `Caddyfile`
- **Local Development:** Use `docker-compose.local.yml` and `Caddyfile.local`

## Next Steps

1. Set up your Supabase project
2. Configure all required API keys
3. Run the initial database migrations
4. Start developing!

For more detailed information, see the main README.md and backend documentation.
