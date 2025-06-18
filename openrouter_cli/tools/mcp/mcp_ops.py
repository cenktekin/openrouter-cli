import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from rich.console import Console
from rich.logging import RichHandler

from ..file_operations.base import FileOperationsTool
from .mcp_client import MCPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("mcp_ops")

class MCPFileOperations(FileOperationsTool):
    """Enhanced file operations using MCP server integration."""

    def __init__(
        self,
        base_dir: str,
        api_key: str,
        allowed_extensions: Optional[List[str]] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        cache_dir: Optional[str] = None,
        model: str = "anthropic/claude-3-7-sonnet",
        max_workers: int = 4,
        cache_ttl: int = 24 * 60 * 60  # 24 hours
    ):
        super().__init__(base_dir, allowed_extensions, max_file_size)
        self.api_key = api_key
        self.cache_dir = Path(cache_dir) if cache_dir else Path(base_dir) / ".cache"
        self.model = model
        self.max_workers = max_workers
        self.cache_ttl = cache_ttl
        self.console = Console()
        self._client: Optional[MCPClient] = None

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    async def client(self) -> MCPClient:
        """Get or create MCP client instance."""
        if self._client is None:
            self._client = MCPClient(
                api_key=self.api_key,
                base_dir=str(self.base_dir),
                model=self.model
            )
            server_config = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", str(self.base_dir)],
                "env": None
            }
            await self._client.connect_to_server(server_config)
        return self._client

    async def use_tool(self, tool_name: str, **kwargs) -> Any:
        """Use a specific MCP tool."""
        try:
            client = await self.client
            tools = client.list_tools()

            # Find the requested tool
            tool = next((t for t in tools if t["function"]["name"] == tool_name), None)
            if not tool:
                raise ValueError(f"Tool not found: {tool_name}")

            # Process query with the specific tool
            result = await client.process_query(
                f"Use the {tool_name} tool with the following parameters: {json.dumps(kwargs)}",
                tools=[tool]
            )

            return result

        except Exception as e:
            logger.error(f"Error using tool {tool_name}: {str(e)}")
            raise

    async def analyze_file(
        self,
        file_path: Union[str, Path],
        prompt: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Analyze a file using MCP server and AI model."""
        file_path = Path(file_path)
        if not self._is_safe_path(file_path):
            raise ValueError(f"Unsafe file path: {file_path}")

        # Check cache
        if use_cache:
            cached_result = self._get_cached_result(file_path)
            if cached_result:
                return cached_result

        # Validate file
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not self._is_allowed_type(file_path):
            raise ValueError(f"File type not allowed: {file_path.suffix}")

        if file_path.stat().st_size > self.max_file_size:
            raise ValueError(f"File too large: {file_path}")

        try:
            # Get client and process file
            client = await self.client
            result = await client.process_query(
                f"Analyze the file {file_path} with the following prompt: {prompt}"
            )

            # Cache result
            if use_cache:
                self._cache_result(file_path, result)

            return {
                "file_path": str(file_path),
                "analysis": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
            raise

    async def batch_analyze_files(
        self,
        file_paths: List[Union[str, Path]],
        prompt: str,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Analyze multiple files concurrently."""
        async def process_file(file_path: Path) -> Dict[str, Any]:
            try:
                return await self.analyze_file(file_path, prompt, use_cache)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                return {
                    "file_path": str(file_path),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }

        # Convert paths to Path objects
        paths = [Path(p) for p in file_paths]

        # Process files concurrently
        tasks = [process_file(p) for p in paths]
        results = await asyncio.gather(*tasks)

        return results

    def _get_cached_result(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Get cached analysis result if available and not expired."""
        cache_file = self.cache_dir / f"{file_path.name}.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r") as f:
                data = json.load(f)

            # Check if cache is expired
            cache_time = datetime.fromisoformat(data["timestamp"])
            if datetime.now() - cache_time > timedelta(seconds=self.cache_ttl):
                return None

            return data

        except Exception as e:
            logger.warning(f"Error reading cache for {file_path}: {str(e)}")
            return None

    def _cache_result(self, file_path: Path, result: Any) -> None:
        """Cache analysis result."""
        cache_file = self.cache_dir / f"{file_path.name}.json"
        try:
            data = {
                "file_path": str(file_path),
                "analysis": result,
                "timestamp": datetime.now().isoformat()
            }
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.warning(f"Error caching result for {file_path}: {str(e)}")

    async def clear_cache(self, file_path: Optional[Union[str, Path]] = None) -> None:
        """Clear analysis cache for a specific file or all files."""
        if file_path:
            cache_file = self.cache_dir / f"{Path(file_path).name}.json"
            if cache_file.exists():
                cache_file.unlink()
        else:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._client:
            await self._client.cleanup()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
