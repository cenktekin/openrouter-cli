import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI
from rich.console import Console
from rich.logging import RichHandler
from datetime import datetime
import aiohttp
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("mcp_client")

class MCPClient:
    """MCP Client for file operations with OpenRouter integration."""

    def __init__(
        self,
        api_key: str,
        base_dir: str,
        model: str = "anthropic/claude-3-7-sonnet",
        max_retries: int = 3,
        timeout: int = 30
    ):
        self.api_key = api_key
        self.base_dir = Path(base_dir).resolve()
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.console = Console()
        self.messages: List[Dict[str, Any]] = []
        self._tools: Optional[List[Dict[str, Any]]] = None
        self._last_update: Optional[str] = None

        # For SSE connections
        self.session_id = None
        self.address = None
        self.connected = False
        self._sse_task = None
        self._event_queue = asyncio.Queue()
        self._lock = asyncio.Lock()

    async def connect_to_server(self, server_config: Dict[str, Any]) -> None:
        """Connect to the MCP server with the given configuration."""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )
            await self.session.initialize()

            # List available tools
            response = await self.session.list_tools()
            self._tools = [self.convert_tool_format(tool) for tool in response.tools]
            self._last_update = datetime.now().isoformat()
            logger.info(f"Connected to server with tools: {[tool.name for tool in response.tools]}")

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {str(e)}")
            raise

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
            import traceback
            traceback.print_exc()

    async def list_tools_sse(self):
        """List available tools from the server via SSE."""
        if not self.connected or not self.session_id:
            raise ConnectionError("Not connected to server")

        return await self._send_request({
            "type": "list_tools"
        })

    async def call_tool_sse(self, tool_name, args):
        """Call a tool with the given arguments via SSE."""
        if not self.connected or not self.session_id:
            raise ConnectionError("Not connected to server")

        return await self._send_request({
            "type": "call_tool",
            "tool": tool_name,
            "arguments": args
        })

    async def _send_request(self, request_data):
        """Send a request to the MCP server via SSE."""
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

    def convert_tool_format(self, tool: Any) -> Dict[str, Any]:
        """Convert MCP tool definition to OpenAI-compatible format."""
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": tool.inputSchema["properties"],
                    "required": tool.inputSchema["required"]
                }
            }
        }

    async def process_query(
        self,
        query: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Process a query using the MCP server and OpenRouter."""
        try:
            # Add user message
            self.messages.append({
                "role": "user",
                "content": query
            })

            # Get available tools if not provided
            if tools is None:
                tools = self._tools or []
                if not tools:
                    response = await self.session.list_tools()
                    tools = [self.convert_tool_format(tool) for tool in response.tools]
                    self._tools = tools
                    self._last_update = datetime.now().isoformat()

            # Get model response
            response = self.openai.chat.completions.create(
                model=self.model,
                tools=tools,
                messages=self.messages,
                timeout=self.timeout
            )

            # Process tool calls
            message = response.choices[0].message
            self.messages.append(message.model_dump())

            if message.tool_calls:
                return await self._handle_tool_calls(message)
            else:
                return message.content

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise

    async def _handle_tool_calls(self, message: Any) -> str:
        """Handle tool calls from the model response."""
        final_text = []

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            try:
                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                # Add tool response to messages
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": result.content
                })

            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {str(e)}")
                result = None

        # Get final response
        response = self.openai.chat.completions.create(
            model=self.model,
            max_tokens=1000,
            messages=self.messages
        )

        final_text.append(response.choices[0].message.content)
        return "\n".join(final_text)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        if not self._tools:
            logger.warning("No tools available. Connect to server first.")
            return []
        return self._tools

    def get_status(self) -> Dict[str, Any]:
        """Get current MCP client status."""
        return {
            "connected": self.session is not None or self.connected,
            "status": "Connected" if (self.session is not None or self.connected) else "Disconnected",
            "tools_count": len(self._tools) if self._tools else 0,
            "last_update": self._last_update or "Never",
            "session_id": self.session_id,
            "address": self.address
        }

    async def cleanup(self) -> None:
        """Clean up resources and close connections."""
        await self.disconnect()
        await self.exit_stack.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
