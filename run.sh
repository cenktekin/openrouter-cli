#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
fi

source venv/bin/activate

if [ ! -f ".env" ] && [ ! -f ".env.example" ]; then
    echo "Warning: .env file not found"
    echo "Please create .env file with OPENROUTER_API_KEY"
elif [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please edit .env file and add your OPENROUTER_API_KEY"
fi

python run.py
