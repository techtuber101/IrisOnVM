#!/usr/bin/env python3

import subprocess
import sys
import platform

IS_WINDOWS = platform.system() == "Windows"

# --- ANSI Colors ---
class Colors:
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"

def check_docker_available():
    """Check if Docker is available and running."""
    try:
        result = subprocess.run(["docker", "version"], capture_output=True, shell=IS_WINDOWS, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{Colors.RED}❌ Docker is not running or not installed.{Colors.ENDC}")
        print(f"{Colors.YELLOW}Please start Docker and try again.{Colors.ENDC}")
        return False

def main():
    if "--help" in sys.argv:
        print("Usage: ./rebuild-production.py")
        print("Rebuild and restart production services using production environment files")
        print("\nSteps:")
        print("  1. docker compose build")
        print("  2. docker compose down")
        print("  3. docker compose up -d")
        print("\nEnvironment files used:")
        print("  - backend/.env")
        print("  - frontend/.env.production")
        return

    if not check_docker_available():
        return

    print(f"{Colors.BLUE}{Colors.BOLD}Rebuilding production environment...{Colors.ENDC}")
    print(f"{Colors.CYAN}Using backend/.env and frontend/.env.production{Colors.ENDC}")
    
    # Step 1: Build
    print(f"{Colors.YELLOW}Step 1: Building images...{Colors.ENDC}")
    subprocess.run(["docker", "compose", "build"], shell=IS_WINDOWS)
    
    # Step 2: Stop
    print(f"{Colors.YELLOW}Step 2: Stopping services...{Colors.ENDC}")
    subprocess.run(["docker", "compose", "down"], shell=IS_WINDOWS)
    
    # Step 3: Start
    print(f"{Colors.YELLOW}Step 3: Starting services...{Colors.ENDC}")
    subprocess.run(["docker", "compose", "up", "-d"], shell=IS_WINDOWS)
    
    print(f"{Colors.GREEN}✅ Production environment rebuilt and started.{Colors.ENDC}")
    print(f"{Colors.CYAN}🌐 Access Iris at: https://irisvision.ai{Colors.ENDC}")

if __name__ == "__main__":
    main()
