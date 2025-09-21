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

def check_docker_compose_up():
    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose.local.yml", "ps", "-q"],
        capture_output=True,
        text=True,
        shell=IS_WINDOWS,
    )
    return len(result.stdout.strip()) > 0

def main():
    if "--help" in sys.argv:
        print("Usage: ./start-local.py [OPTION]")
        print("Manage Iris local development services")
        print("\nOptions:")
        print("  start\tStart local development environment (default)")
        print("  stop\tStop local development environment")
        print("  restart\tRestart local development environment")
        print("  logs\tShow logs from all services")
        print("  --help\tShow this help message")
        return

    if not check_docker_available():
        return

    action = "start"
    if len(sys.argv) > 1:
        action = sys.argv[1]

    if action == "stop":
        print(f"{Colors.BLUE}{Colors.BOLD}Stopping local development environment...{Colors.ENDC}")
        subprocess.run(["docker", "compose", "-f", "docker-compose.local.yml", "down"], shell=IS_WINDOWS)
        print(f"{Colors.GREEN}✅ Local development environment stopped.{Colors.ENDC}")
        
    elif action == "restart":
        print(f"{Colors.BLUE}{Colors.BOLD}Restarting local development environment...{Colors.ENDC}")
        subprocess.run(["docker", "compose", "-f", "docker-compose.local.yml", "down"], shell=IS_WINDOWS)
        subprocess.run(["docker", "compose", "-f", "docker-compose.local.yml", "up", "-d"], shell=IS_WINDOWS)
        print(f"{Colors.GREEN}✅ Local development environment restarted.{Colors.ENDC}")
        print(f"{Colors.CYAN}🌐 Access Iris at: http://localhost:3000{Colors.ENDC}")
        
    elif action == "logs":
        print(f"{Colors.BLUE}{Colors.BOLD}Showing logs from local development environment...{Colors.ENDC}")
        subprocess.run(["docker", "compose", "-f", "docker-compose.local.yml", "logs", "-f"], shell=IS_WINDOWS)
        
    else:  # start
        is_up = check_docker_compose_up()
        
        if is_up:
            print(f"{Colors.YELLOW}⚠️  Local development environment is already running.{Colors.ENDC}")
            print(f"{Colors.CYAN}Use './start-local.py stop' to stop it first.{Colors.ENDC}")
            return

        print(f"{Colors.BLUE}{Colors.BOLD}Starting local development environment...{Colors.ENDC}")
        subprocess.run(["docker", "compose", "-f", "docker-compose.local.yml", "up", "-d"], shell=IS_WINDOWS)
        print(f"{Colors.GREEN}✅ Local development environment started.{Colors.ENDC}")
        print(f"{Colors.CYAN}🌐 Access Iris at: http://localhost:3000{Colors.ENDC}")
        print(f"{Colors.CYAN}📊 Backend API at: http://localhost:8000/api{Colors.ENDC}")
        print(f"{Colors.CYAN}❤️  Health check at: http://localhost/health{Colors.ENDC}")

if __name__ == "__main__":
    main()