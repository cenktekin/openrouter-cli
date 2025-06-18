#!/bin/bash

# AI-powered file operations wrapper script
# This script provides a user-friendly interface for the AI file operations tool

# Default configuration
DEFAULT_BASE_DIR="."
DEFAULT_CACHE_DIR=".ai_cache"
DEFAULT_MAX_SIZE=10
DEFAULT_WORKERS=4

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display help message
show_help() {
    echo -e "${BLUE}AI-powered File Operations Tool${NC}"
    echo
    echo "Usage: $0 [command] [options]"
    echo
    echo "Commands:"
    echo "  image <path>              Analyze a single image"
    echo "  pdf <path>                Analyze a single PDF"
    echo "  batch-images <paths...>   Analyze multiple images"
    echo "  batch-pdfs <paths...>     Analyze multiple PDFs"
    echo "  cache clear [type]        Clear cache (type: image, pdf, or all)"
    echo "  cache stats               Show cache statistics"
    echo
    echo "Options:"
    echo "  --api-key KEY             OpenRouter API key"
    echo "  --base-dir DIR            Base directory for operations"
    echo "  --cache-dir DIR           Cache directory"
    echo "  --max-size MB             Maximum file size in MB"
    echo "  --workers N               Number of concurrent workers"
    echo "  --prompt TEXT             Custom prompt for analysis"
    echo "  --model TYPE              Model type to use"
    echo "  --no-cache                Disable result caching"
    echo
    echo "Examples:"
    echo "  $0 image photo.jpg --prompt \"Describe this image in detail\""
    echo "  $0 pdf document.pdf --model summary"
    echo "  $0 batch-images *.jpg --workers 8"
    echo "  $0 cache stats"
}

# Function to check if Python and required packages are installed
check_dependencies() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is not installed${NC}"
        exit 1
    fi

    # Check for required Python packages
    local missing_packages=()
    for package in "requests" "tqdm" "cryptography"; do
        if ! python3 -c "import $package" &> /dev/null; then
            missing_packages+=("$package")
        fi
    done

    if [ ${#missing_packages[@]} -ne 0 ]; then
        echo -e "${YELLOW}Installing missing packages: ${missing_packages[*]}${NC}"
        pip3 install "${missing_packages[@]}"
    fi
}

# Function to validate file paths
validate_paths() {
    local paths=("$@")
    for path in "${paths[@]}"; do
        if [ ! -f "$path" ]; then
            echo -e "${RED}Error: File not found: $path${NC}"
            exit 1
        fi
    done
}

# Function to create cache directory if it doesn't exist
setup_cache() {
    if [ ! -d "$CACHE_DIR" ]; then
        echo -e "${YELLOW}Creating cache directory: $CACHE_DIR${NC}"
        mkdir -p "$CACHE_DIR"
    fi
}

# Main script execution
main() {
    # Check dependencies
    check_dependencies

    # Parse command line arguments
    local command=""
    local paths=()
    local api_key=""
    local base_dir="$DEFAULT_BASE_DIR"
    local cache_dir="$DEFAULT_CACHE_DIR"
    local max_size="$DEFAULT_MAX_SIZE"
    local workers="$DEFAULT_WORKERS"
    local prompt=""
    local model=""
    local no_cache=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            image|pdf|batch-images|batch-pdfs|cache)
                command="$1"
                shift
                ;;
            --api-key)
                api_key="$2"
                shift 2
                ;;
            --base-dir)
                base_dir="$2"
                shift 2
                ;;
            --cache-dir)
                cache_dir="$2"
                shift 2
                ;;
            --max-size)
                max_size="$2"
                shift 2
                ;;
            --workers)
                workers="$2"
                shift 2
                ;;
            --prompt)
                prompt="--prompt \"$2\""
                shift 2
                ;;
            --model)
                model="--model $2"
                shift 2
                ;;
            --no-cache)
                no_cache="--no-cache"
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                paths+=("$1")
                shift
                ;;
        esac
    done

    # Validate command
    if [ -z "$command" ]; then
        echo -e "${RED}Error: No command specified${NC}"
        show_help
        exit 1
    fi

    # Setup cache directory
    setup_cache

    # Validate paths for file operations
    if [[ "$command" =~ ^(image|pdf|batch-images|batch-pdfs)$ ]]; then
        validate_paths "${paths[@]}"
    fi

    # Construct Python command
    local python_cmd="python3 -m tools.file_operations.cli $command"

    # Add paths
    for path in "${paths[@]}"; do
        python_cmd+=" \"$path\""
    done

    # Add options
    [ -n "$api_key" ] && python_cmd+=" --api-key \"$api_key\""
    [ -n "$base_dir" ] && python_cmd+=" --base-dir \"$base_dir\""
    [ -n "$cache_dir" ] && python_cmd+=" --cache-dir \"$cache_dir\""
    [ -n "$max_size" ] && python_cmd+=" --max-size $max_size"
    [ -n "$workers" ] && python_cmd+=" --workers $workers"
    [ -n "$prompt" ] && python_cmd+=" $prompt"
    [ -n "$model" ] && python_cmd+=" $model"
    [ -n "$no_cache" ] && python_cmd+=" $no_cache"

    # Execute command
    echo -e "${GREEN}Executing: $python_cmd${NC}"
    eval "$python_cmd"
}

# Run main function
main "$@"
