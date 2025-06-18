import asyncio
import logging
import json
import traceback
import uuid
import aiohttp
from rich.console import Console
from rich.table import Table

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()

class MCPClient:
    """Simple MCP Client for connecting to MCP server via SSE."""

    def __init__(self):
        self.session_id = None
        self.address = None
        self.connected = False
        self._sse_task = None
        self._event_queue = asyncio.Queue()
        self._lock = asyncio.Lock()

    async def connect(self, address):
        """Connect to MCP server via SSE."""
        async with self._lock:
            if self.connected:
                await self.disconnect()

            self.address = address
            self.connected = False
            self.session_id = None

            # Start SSE connection in background
            self._sse_task = asyncio.create_task(self._handle_sse_events())

            # Wait for session_id to be received
            try:
                start_time = asyncio.get_event_loop().time()
                timeout = 5.0  # seconds

                while self.session_id is None:
                    if (asyncio.get_event_loop().time() - start_time) > timeout:
                        raise TimeoutError("Timed out waiting for session_id")
                    await asyncio.sleep(0.1)

                self.connected = True
                return True
            except Exception as e:
                await self.disconnect()
                raise ConnectionError(f"Failed to connect: {e}")

    async def disconnect(self):
        """Disconnect from MCP server."""
        if self._sse_task:
            self._sse_task.cancel()
            try:
                await self._sse_task
            except asyncio.CancelledError:
                pass
            self._sse_task = None

        self.connected = False
        self.session_id = None
        self.address = None
        logger.info("Disconnected from MCP server")

    async def _handle_sse_events(self):
        """Background task to handle SSE events."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.address) as response:
                    if response.status != 200:
                        raise ConnectionError(f"Failed to connect: HTTP {response.status}")

                    logger.info(f"SSE connection established to {self.address}")

                    # Process SSE events
                    event_data = None
                    event_type = None
                    event_id = None

                    async for line in response.content:
                        line = line.decode('utf-8').strip()

                        # Empty line marks the end of an event
                        if not line:
                            if event_data:
                                try:
                                    # Parse the event data as JSON
                                    data = json.loads(event_data)

                                    # Extract session_id from connection event
                                    if event_type == "connection":
                                        if "session_id" in data:
                                            self.session_id = data["session_id"]
                                            logger.info(f"Received session_id: {self.session_id}")

                                    # Queue the event for processing
                                    await self._event_queue.put({
                                        "type": event_type,
                                        "id": event_id,
                                        "data": data
                                    })

                                except json.JSONDecodeError as e:
                                    logger.warning(f"Invalid JSON in SSE event: {event_data} - Error: {e}")
                                except Exception as e:
                                    logger.error(f"Error processing SSE event: {e}")

                                # Reset for next event
                                event_data = None
                                event_type = None
                                event_id = None
                            continue

                        # Parse SSE fields
                        if line.startswith('data:'):
                            event_data = line[5:].strip()  # Remove 'data: ' prefix
                        elif line.startswith('event:'):
                            event_type = line[6:].strip()  # Remove 'event: ' prefix
                        elif line.startswith('id:'):
                            event_id = line[3:].strip()  # Remove 'id: ' prefix

        except asyncio.CancelledError:
            logger.info("SSE event handler cancelled")
        except Exception as e:
            logger.error(f"SSE connection error: {e}")
            traceback.print_exc()

    async def list_tools(self):
        """List available tools from the server."""
        if not self.connected or not self.session_id:
            raise ConnectionError("Not connected to server")

        return await self._send_request({
            "type": "list_tools"
        })

    async def call_tool(self, tool_name, args):
        """Call a tool with the given arguments."""
        if not self.connected or not self.session_id:
            raise ConnectionError("Not connected to server")

        return await self._send_request({
            "type": "call_tool",
            "tool": tool_name,
            "arguments": args
        })

    async def _send_request(self, request_data):
        """Send a request to the MCP server."""
        if not self.connected or not self.session_id:
            raise ConnectionError("Not connected to server")

        # Add session_id and request_id
        request_data["session_id"] = self.session_id
        request_data["request_id"] = str(uuid.uuid4())

        # Extract base URL (remove /sse if present)
        base_url = self.address.rsplit('/sse', 1)[0]

        # Send POST request
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{base_url}/messages", json=request_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Server returned {response.status}: {error_text}")
                    raise ConnectionError(f"Request failed: HTTP {response.status}")

                return await response.json()

async def main():
    """Main function to demonstrate MCP client usage."""
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
                    table = Table(title="MCP Tools")
                    table.add_column("Name", style="cyan")
                    table.add_column("Description", style="green")

                    for tool in tools:
                        name = tool.get("name", "Unknown")
                        desc = tool.get("description", "No description")
                        table.add_row(name, desc)

                    console.print(table)

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
                traceback.print_exc()

            # Process events
            console.print("[yellow]Listening for events (press Ctrl+C to exit)...[/yellow]")
            try:
                while True:
                    event = await client._event_queue.get()
                    console.print(f"[blue]Event received:[/blue] {event}")
            except KeyboardInterrupt:
                console.print("[yellow]Keyboard interrupt received, exiting...[/yellow]")
            except Exception as e:
                console.print(f"[red]Error processing events: {str(e)}[/red]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        traceback.print_exc()
    finally:
        await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[yellow]Interrupted by user, exiting...[/yellow]")
