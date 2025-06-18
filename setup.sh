#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display help message
show_help() {
    echo -e "${BLUE}AI File Analyzer Setup Script${NC}"
    echo
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  --api-key KEY     Set OpenRouter API key"
    echo "  --docker          Setup using Docker"
    echo "  --local           Setup for local development"
    echo "  --monitoring      Include monitoring stack (Prometheus + Grafana)"
    echo "  --help           Show this help message"
}

# Function to check dependencies
check_dependencies() {
    local missing_deps=()

    # Check for Docker if --docker is specified
    if [ "$USE_DOCKER" = true ]; then
        if ! command -v docker &> /dev/null; then
            missing_deps+=("docker")
        fi
        if ! command -v docker-compose &> /dev/null; then
            missing_deps+=("docker-compose")
        fi
    else
        # Check for Python dependencies
        if ! command -v python3 &> /dev/null; then
            missing_deps+=("python3")
        fi
        if ! command -v pip3 &> /dev/null; then
            missing_deps+=("pip3")
        fi
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${RED}Error: Missing dependencies: ${missing_deps[*]}${NC}"
        exit 1
    fi
}

# Function to create necessary directories
create_directories() {
    echo -e "${YELLOW}Creating necessary directories...${NC}"
    mkdir -p data .ai_cache exports logs
}

# Function to setup local environment
setup_local() {
    echo -e "${YELLOW}Setting up local environment...${NC}"

    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt

    # Create .env file
    if [ -n "$API_KEY" ]; then
        echo "OPENROUTER_API_KEY=$API_KEY" > .env
    fi

    echo -e "${GREEN}Local setup complete!${NC}"
    echo "To activate the environment, run: source venv/bin/activate"
}

# Function to setup Docker environment
setup_docker() {
    echo -e "${YELLOW}Setting up Docker environment...${NC}"

    # Create .env file for Docker
    if [ -n "$API_KEY" ]; then
        echo "OPENROUTER_API_KEY=$API_KEY" > .env
    fi

    # Build and start containers
    if [ "$USE_MONITORING" = true ]; then
        docker-compose up -d
    else
        docker-compose up -d ai-analyzer
    fi

    echo -e "${GREEN}Docker setup complete!${NC}"
    echo "To view logs, run: docker-compose logs -f"
}

# Parse command line arguments
USE_DOCKER=false
USE_MONITORING=false
API_KEY=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --api-key)
            API_KEY="$2"
            shift 2
            ;;
        --docker)
            USE_DOCKER=true
            shift
            ;;
        --local)
            USE_DOCKER=false
            shift
            ;;
        --monitoring)
            USE_MONITORING=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Check if API key is provided
if [ -z "$API_KEY" ]; then
    echo -e "${YELLOW}Warning: No API key provided${NC}"
    echo "You can set it later in the .env file or config.yaml"
fi

# Check dependencies
check_dependencies

# Create directories
create_directories

# Setup environment
if [ "$USE_DOCKER" = true ]; then
    setup_docker
else
    setup_local
fi

# Print final instructions
echo -e "\n${BLUE}Setup Complete!${NC}"
echo -e "To get started:"
if [ "$USE_DOCKER" = true ]; then
    echo "1. Your files should be placed in the 'data' directory"
    echo "2. Run analysis using: docker-compose exec ai-analyzer python -m tools.file_operations.cli [command]"
    if [ "$USE_MONITORING" = true ]; then
        echo "3. View metrics at: http://localhost:9090 (Prometheus)"
        echo "4. View dashboards at: http://localhost:3000 (Grafana)"
    fi
else
    echo "1. Activate the virtual environment: source venv/bin/activate"
    echo "2. Run analysis using: python -m tools.file_operations.cli [command]"
fi
echo -e "\nFor more information, run: python -m tools.file_operations.cli --help"
