import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from rich.console import Console

logger = logging.getLogger("mcp_manager")


class MCPServerManager:
    def __init__(self, config_path: Optional[str] = None):
        self.console = Console()
        self.config_path = config_path or self._get_default_config_path()
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.active_connections: Dict[str, Any] = {}
        self._load_config()

    def _get_default_config_path(self) -> Optional[str]:
        possible_paths = [
            Path.cwd() / "mcp_servers.json",
            Path.cwd() / "mcp_config.json",
            Path.home() / ".openrouter-cli" / "mcp_servers.json",
        ]
        for p in possible_paths:
            if p.exists():
                return str(p)
        return None

    def _load_config(self):
        if not self.config_path or not Path(self.config_path).exists():
            logger.info(
                "No MCP config found. Copy mcp_servers.json.example to mcp_servers.json"
            )
            return

        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
                self.servers = config.get("mcpServers", {})
                logger.info(f"Loaded {len(self.servers)} MCP server configs")
        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")

    def list_servers(self) -> List[Dict[str, Any]]:
        result = []
        for name, config in self.servers.items():
            is_active = name in self.active_connections
            result.append(
                {
                    "name": name,
                    "type": config.get("type", "unknown"),
                    "url": config.get("url", config.get("command", "")),
                    "active": is_active,
                }
            )
        return result

    def get_server_config(self, name: str) -> Optional[Dict[str, Any]]:
        return self.servers.get(name)

    async def connect(self, name: str, client: Any) -> bool:
        if name not in self.servers:
            logger.error(f"Server '{name}' not found in config")
            return False

        config = self.servers[name]
        server_type = config.get("type", "sse")

        try:
            if server_type == "sse":
                url = config.get("url")
                if not url:
                    logger.error(f"No URL for SSE server '{name}'")
                    return False
                success = await client.connect_sse(url)
            else:
                command = config.get("command")
                args = config.get("args", [])
                env = config.get("env")

                if not command:
                    logger.error(f"No command for stdio server '{name}'")
                    return False

                server_config = {"command": command, "args": args, "env": env}
                success = await client.connect_stdio(server_config)

            if success:
                self.active_connections[name] = client
                logger.info(f"Connected to MCP server '{name}'")
            return success

        except Exception as e:
            logger.error(f"Failed to connect to '{name}': {e}")
            return False

    async def disconnect(self, name: str, client: Any):
        if name in self.active_connections:
            await client.disconnect()
            del self.active_connections[name]
            logger.info(f"Disconnected from '{name}'")

    async def disconnect_all(self):
        for name in list(self.active_connections.keys()):
            client = self.active_connections[name]
            await client.disconnect()
        self.active_connections.clear()
