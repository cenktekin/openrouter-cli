"""
API Key Manager for OpenRouter CLI.
"""

import os
import json
import random
from pathlib import Path
from typing import List, Optional
from rich.console import Console

console = Console()


class OpenRouterKeyManager:
    """Manages API keys for OpenRouter."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize the key manager with the given config directory."""
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Default to .openrouter in current working directory (project-local)
            self.config_dir = Path.cwd() / ".openrouter"

        self.keys_file = self.config_dir / "keys.json"
        self.keys: List[str] = []
        self.load_keys()

    def load_keys(self) -> None:
        """Load API keys from the keys file."""
        # Create config directory if it doesn't exist
        if not self.config_dir.exists():
            try:
                self.config_dir.mkdir(parents=True, exist_ok=True)
                console.print(
                    f"[green]Created config directory: {self.config_dir}[/green]"
                )
            except Exception as e:
                console.print(f"[red]Error creating config directory: {str(e)}[/red]")
                return

        # Load keys from file
        if self.keys_file.exists():
            try:
                with open(self.keys_file, "r") as f:
                    data = json.load(f)
                    keys_data = data.get("keys", [])
                    # Handle both string and object formats
                    extracted_keys = []
                    for key in keys_data:
                        if isinstance(key, str) and key:
                            extracted_keys.append(key)
                        elif isinstance(key, dict) and "key" in key:
                            key_str = key.get("key")
                            if key_str:
                                extracted_keys.append(key_str)
                    self.keys = extracted_keys
            except Exception as e:
                console.print(f"[red]Error loading API keys: {str(e)}[/red]")

        # Check environment variable as fallback
        env_key = os.environ.get("OPENROUTER_API_KEY")
        if env_key and env_key not in self.keys:
            self.keys.append(env_key)
            console.print("[green]Added API key from environment variable[/green]")

    def save_keys(self) -> bool:
        """Save API keys to the keys file."""
        try:
            with open(self.keys_file, "w") as f:
                json.dump({"keys": self.keys}, f, indent=2)
            return True
        except Exception as e:
            console.print(f"[red]Error saving API keys: {str(e)}[/red]")
            return False

    def add_key(self, key: str) -> bool:
        """Add an API key."""
        if not key:
            console.print("[red]API key cannot be empty[/red]")
            return False

        if key in self.keys:
            console.print("[yellow]API key already exists[/yellow]")
            return True

        self.keys.append(key)
        return self.save_keys()

    def remove_key(self, key: str) -> bool:
        """Remove an API key."""
        if key not in self.keys:
            console.print("[yellow]API key not found[/yellow]")
            return False

        self.keys.remove(key)
        return self.save_keys()

    def list_keys(self) -> List[str]:
        """List all API keys."""
        return [key for key in self.keys if key is not None]

    def get_random_key(self) -> Optional[str]:
        """Get a random API key."""
        if not self.keys:
            console.print("[red]No API keys available[/red]")
            return None

        key_item = random.choice(self.keys)
        if isinstance(key_item, dict):
            return key_item.get("key")
        return key_item

    def get_masked_keys(self) -> List[str]:
        """Get masked versions of the API keys for display."""
        masked_keys = []
        for key in self.keys:
            if key and len(key) > 8:
                masked = key[:4] + "*" * (len(key) - 8) + key[-4:]
            elif key:
                masked = "*" * len(key)
            else:
                continue
            masked_keys.append(masked)
        return masked_keys
