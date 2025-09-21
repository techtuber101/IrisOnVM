#!/usr/bin/env python3

import os
import shutil
import sys

def setup_env_files(env_type="local"):
    """Set up environment files for local or production."""
    
    if env_type == "production":
        print("🔧 Setting up production environment files...")
        backend_env_example = "backend/.env.example"
        backend_env = "backend/.env"
        frontend_env_example = "frontend/.env.production.example"
        frontend_env = "frontend/.env.production"
    else:
        print("🔧 Setting up local development environment files...")
        backend_env_example = "backend/.env.local.example"
        backend_env = "backend/.env.local"
        frontend_env_example = "frontend/.env.local.example"
        frontend_env = "frontend/.env.local"
    
    # Backend environment setup
    if os.path.exists(backend_env_example):
        if not os.path.exists(backend_env):
            shutil.copy(backend_env_example, backend_env)
            print(f"✅ Created {backend_env}")
        else:
            print(f"⚠️  {backend_env} already exists")
    else:
        print(f"❌ {backend_env_example} not found")
    
    # Frontend environment setup
    if os.path.exists(frontend_env_example):
        if not os.path.exists(frontend_env):
            shutil.copy(frontend_env_example, frontend_env)
            print(f"✅ Created {frontend_env}")
        else:
            print(f"⚠️  {frontend_env} already exists")
    else:
        print(f"❌ {frontend_env_example} not found")
    
    if env_type == "production":
        print("\n🔧 Next steps:")
        print("1. Edit backend/.env with your Supabase credentials and API keys")
        print("2. Edit frontend/.env.production with your Supabase credentials")
        print("3. Run 'docker compose up -d' to start the production environment")
    else:
        print("\n🔧 Next steps:")
        print("1. Edit backend/.env.local with your Supabase credentials and API keys")
        print("2. Edit frontend/.env.local with your Supabase credentials")
        print("3. Run './start-local.py' to start the development environment")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "production":
        setup_env_files("production")
    else:
        setup_env_files("local")

if __name__ == "__main__":
    main()
