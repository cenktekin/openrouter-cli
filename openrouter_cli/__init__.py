"""OpenRouter CLI - A command-line interface for OpenRouter's API."""

__version__ = "0.0.1"

from openrouter_cli.key_manager import OpenRouterKeyManager
from openrouter_cli.main import main

__all__ = ['OpenRouterKeyManager', 'main']
