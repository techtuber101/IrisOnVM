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
        print("Usage: ./start-production.py")
        print("Restart production services using production environment files")
        print("\nEnvironment files used:")
        print("  - backend/.env")
        print("  - frontend/.env.production")
        return

    if not check_docker_available():
        return

    print(f"{Colors.BLUE}{Colors.BOLD}Restarting production environment...{Colors.ENDC}")
    print(f"{Colors.CYAN}Using backend/.env and frontend/.env.production{Colors.ENDC}")
    
    subprocess.run(["docker", "compose", "restart"], shell=IS_WINDOWS)
    
    print(f"{Colors.GREEN}✅ Production environment restarted.{Colors.ENDC}")
    print(f"{Colors.CYAN}🌐 Access Iris at: https://irisvision.ai{Colors.ENDC}")

if __name__ == "__main__":
    main()