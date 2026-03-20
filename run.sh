#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
fi

source venv/bin/activate

if [ ! -f ".env" ] && [ -z "$OPENROUTER_API_KEY" ]; then
    echo "Warning: .env file not found and OPENROUTER_API_KEY not set"
    echo "Please create .env file or set OPENROUTER_API_KEY environment variable"
fi

python run.py
