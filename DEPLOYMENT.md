# 🚀 Google Cloud VM Deployment Guide for irisvision.ai

## Prerequisites

1. **Google Cloud VM Instance** with:
   - Ubuntu 20.04+ or Debian 11+
   - At least 4GB RAM, 2 CPU cores
   - 20GB+ disk space
   - Docker and Docker Compose installed

2. **Domain Configuration**:
   - Point `irisvision.ai` and `www.irisvision.ai` to your VM's public IP
   - Ensure ports 80 and 443 are open in firewall

## Quick Deployment Steps

### 1. Upload Code to VM
```bash
# On your local machine
scp -r /path/to/IrisOnVM user@your-vm-ip:/home/user/
```

### 2. Configure Environment Variables
```bash
# On the VM
cd /home/user/IrisOnVM

# Copy and configure backend environment
cp production.env.example backend/.env
nano backend/.env  # Fill in your actual values

# Copy and configure frontend environment  
cp frontend.env.production.example frontend/.env.local
nano frontend/.env.local  # Fill in your actual values
```

### 3. Required Environment Variables

**Backend (.env):**
- `ENV_MODE=production`
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Your Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` - At least one LLM provider
- `TAVILY_API_KEY` - For web search functionality
- `FIRECRAWL_API_KEY` - For web scraping
- `DAYTONA_API_KEY` - For agent execution
- `WEBHOOK_BASE_URL=https://irisvision.ai`

**Frontend (.env.local):**
- `NEXT_PUBLIC_SUPABASE_URL` - Same as backend
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Same as backend
- `NEXT_PUBLIC_BACKEND_URL=https://irisvision.ai/api`
- `NEXT_PUBLIC_URL=https://irisvision.ai`
- `NEXT_PUBLIC_ENV_MODE=PRODUCTION`

### 4. Deploy with Docker Compose
```bash
# Build and start all services
docker compose up -d --build

# Check logs
docker compose logs -f

# Verify services are running
docker compose ps

# Check Caddy logs specifically
docker compose logs caddy
```

### 5. Verify Deployment
- Visit `https://irisvision.ai` - should load the frontend
- Visit `https://irisvision.ai/api/health` - should return "OK"
- Check SSL certificate is working

## Configuration Summary

✅ **Caddyfile**: Already configured for irisvision.ai domain
✅ **CORS Origins**: Updated to include irisvision.ai
✅ **Supabase Config**: Updated site_url to https://irisvision.ai
✅ **Environment Templates**: Created for easy configuration

## Troubleshooting

### Common Issues:
1. **SSL Certificate Issues**: Caddy automatically handles SSL via Let's Encrypt
2. **CORS Errors**: Ensure irisvision.ai is in allowed origins
3. **Database Connection**: Verify Supabase credentials
4. **Port Conflicts**: Ensure ports 80, 443, 3000, 8000 are available

### Useful Commands:
```bash
# Restart services
docker compose restart

# View logs
docker compose logs backend
docker compose logs frontend

# Check service health
curl https://irisvision.ai/api/health

# Rebuild specific service
docker compose up -d --build backend
```

## Security Notes

- The Caddyfile includes security headers
- Redis is bound to localhost only
- All services run in Docker containers
- SSL/TLS is automatically configured

## Monitoring

- Check `docker compose logs` for any errors
- Monitor VM resources (CPU, RAM, disk)
- Set up log rotation for production use

Your irisvision.ai deployment should now be live! 🎉
