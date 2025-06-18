"""
OpenRouter CLI - A command-line interface for OpenRouter's API.
"""

__version__ = "0.0.1"

from openrouter_cli.key_manager import OpenRouterKeyManager
from openrouter_cli.schema_manager import SchemaManager
from openrouter_cli.tools.openrouter_client import create_client

# Main entry point
from openrouter_cli.main import main

__all__ = [
    'OpenRouterKeyManager',
    'SchemaManager',
    'create_client',
    'main',
]
