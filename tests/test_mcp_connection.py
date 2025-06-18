import asyncio
import logging
import sys
from mcp_client import MCPClient
from rich.console import Console

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()

async def main():
    """Test MCP client connection."""
    client = MCPClient()
    server_address = "http://localhost:8000/sse"

    try:
        console.print(f"[yellow]Connecting to MCP server at {server_address}...[/yellow]")
        if await client.connect(server_address):
            console.print(f"[green]Connected to MCP server at {server_address}[/green]")
            console.print(f"[green]Session ID: {client.session_id}[/green]")

            # List available tools
            console.print("[yellow]Listing available tools...[/yellow]")
            try:
                response = await client.list_tools()
                tools = response.get("tools", [])

                if tools:
                    console.print(f"[green]Found {len(tools)} tools:[/green]")
                    for tool in tools:
                        name = tool.get("name", "Unknown")
                        desc = tool.get("description", "No description")
                        console.print(f"[cyan]{name}[/cyan]: {desc}")

                    # Try using the echo tool
                    echo_tool = next((t for t in tools if t["name"] == "echo"), None)
                    if echo_tool:
                        console.print("[yellow]Testing echo tool...[/yellow]")
                        result = await client.call_tool("echo", {"text": "Hello, MCP!"})
                        console.print(f"[green]Echo result:[/green] {result}")
                else:
                    console.print("[yellow]No tools available[/yellow]")
            except Exception as e:
                console.print(f"[red]Error listing tools: {str(e)}[/red]")

            # Disconnect
            await client.disconnect()
            console.print("[yellow]Disconnected from MCP server[/yellow]")
        else:
            console.print(f"[red]Failed to connect to MCP server[/red]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
    finally:
        if client.connected:
            await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[yellow]Interrupted by user, exiting...[/yellow]")
    sys.exit(0)
