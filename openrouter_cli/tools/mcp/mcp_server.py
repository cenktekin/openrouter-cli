import anyio
import click
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.logging import RichHandler
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from mcp.shared._httpx_utils import create_mcp_http_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("mcp_server")

class MCPServer:
    """MCP Server implementation with support for multiple transports."""

    def __init__(
        self,
        name: str = "openrouter-mcp-server",
        config_path: Optional[str] = None
    ):
        self.name = name
        self.console = Console()
        self.config = self._load_config(config_path)
        self.server = Server(name)
        self._register_tools()

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load server configuration from YAML file."""
        if not config_path:
            # Path(__file__).parent.parent = openrouter_cli
            config_path = Path(__file__).parent.parent / "config" / "mcp_config.yaml"
            print(f"MCP server config path: {config_path}")

        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
            return {}

    def _register_tools(self):
        """Register available tools with the server."""

        @self.server.call_tool()
        async def fetch_tool(
            name: str, arguments: dict
        ) -> List[TextContent | ImageContent | EmbeddedResource]:
            """Fetch tool implementation."""
            if name != "fetch":
                raise ValueError(f"Unknown tool: {name}")
            if "url" not in arguments:
                raise ValueError("Missing required argument 'url'")
            return await self._fetch_website(arguments["url"])

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="fetch",
                    description="Fetches a website and returns its content",
                    inputSchema={
                        "type": "object",
                        "required": ["url"],
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL to fetch",
                            }
                        },
                    },
                )
            ]

    async def _fetch_website(
        self,
        url: str,
    ) -> List[TextContent | ImageContent | EmbeddedResource]:
        """Fetch website content."""
        headers = {
            "User-Agent": "OpenRouter MCP Server"
        }
        async with create_mcp_http_client(headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            return [TextContent(type="text", text=response.text)]

    async def run_stdio(self):
        """Run server with stdio transport."""
        async with stdio_server() as streams:
            await self.server.run(
                streams[0],
                streams[1],
                self.server.create_initialization_options()
            )

    async def run_sse(self, port: int = 8000, host: str = "0.0.0.0"):
        """Run server with SSE transport and print its address."""
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await self.server.run(
                    streams[0],
                    streams[1],
                    self.server.create_initialization_options()
                )
            return Response()

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn
        address = f"http://{host if host != '0.0.0.0' else 'localhost'}:{port}/sse"
        print(f"[MCP Server] SSE/HTTP server running at: {address}")
        uvicorn.run(starlette_app, host=host, port=port)

    def run_sse_sync(self, port: int = 8000, host: str = "0.0.0.0"):
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await self.server.run(
                    streams[0],
                    streams[1],
                    self.server.create_initialization_options()
                )
            return Response()

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn
        address = f"http://{host if host != '0.0.0.0' else 'localhost'}:{port}/sse"
        print(f"[MCP Server] SSE/HTTP server running at: {address}")
        uvicorn.run(starlette_app, host=host, port=port)

def start_server(transport: str = "stdio", port: int = 8000, host: str = "0.0.0.0"):
    """Start MCP server with specified transport and print address if SSE."""
    server = MCPServer()

    if transport == "sse":
        server.run_sse_sync(port, host)
    else:
        print("[MCP Server] stdio server running (no network address)")
        import anyio
        anyio.run(server.run_stdio)

if __name__ == "__main__":
    import click

    @click.command()
    @click.option("--port", default=8000, help="Port to listen on for SSE")
    @click.option(
        "--transport",
        type=click.Choice(["stdio", "sse"]),
        default="stdio",
        help="Transport type",
    )
    @click.option("--host", default="0.0.0.0", help="Host to bind for SSE")
    def main(port: int, transport: str, host: str):
        start_server(transport, port, host)

    main()
