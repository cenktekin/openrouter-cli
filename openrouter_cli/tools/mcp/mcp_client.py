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
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("mcp_client")


class MCPClient:
    def __init__(
        self,
        api_key: str,
        base_dir: str,
        model: Optional[str] = None,
        timeout: int = 60,
    ):
        self.api_key = api_key
        self.base_dir = Path(base_dir).resolve()
        self.model = model
        self.timeout = timeout
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        self.console = Console()
        self.messages: List[Dict[str, Any]] = []
        self._tools: Optional[List[Dict[str, Any]]] = None
        self._last_update: Optional[str] = None
        self.session_id = None
        self.address = None
        self.connected = False
        self._sse_task = None
        self._event_queue = asyncio.Queue()
        self._lock = asyncio.Lock()
        self.transport_type: Optional[str] = None

    async def connect_stdio(self, server_config: Dict[str, Any]) -> bool:
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
            response = await self.session.list_tools()
            self._tools = [self._convert_tool_format(tool) for tool in response.tools]
            self._last_update = datetime.now().isoformat()
            self.transport_type = "stdio"
            self.connected = True
            logger.info(
                f"Connected via stdio. Tools: {[t['function']['name'] for t in self._tools]}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect via stdio: {e}")
            return False

    async def connect_sse(self, url: str) -> bool:
        async with self._lock:
            if self.connected:
                await self.disconnect()
            self.address = url
            self.connected = False
            self.session_id = None
            self._sse_task = asyncio.create_task(self._handle_sse_events())
            try:
                start_time = asyncio.get_event_loop().time()
                timeout = 10.0
                while self.session_id is None:
                    if (asyncio.get_event_loop().time() - start_time) > timeout:
                        raise TimeoutError("Timed out waiting for session_id")
                    await asyncio.sleep(0.1)
                self.connected = True
                self.transport_type = "sse"
                return True
            except Exception as e:
                await self.disconnect()
                raise ConnectionError(f"Failed to connect: {e}")

    async def disconnect(self):
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
        self.transport_type = None
        logger.info("Disconnected from MCP server")

    async def _handle_sse_events(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.address) as response:
                    if response.status != 200:
                        raise ConnectionError(f"HTTP {response.status}")
                    logger.info(f"SSE connected to {self.address}")
                    event_data = None
                    event_type = None
                    async for line in response.content:
                        line = line.decode("utf-8").strip()
                        if not line:
                            if event_data:
                                try:
                                    data = json.loads(event_data)
                                    if (
                                        event_type == "connection"
                                        and "session_id" in data
                                    ):
                                        self.session_id = data["session_id"]
                                        logger.info(f"session_id: {self.session_id}")
                                    await self._event_queue.put(
                                        {"type": event_type, "data": data}
                                    )
                                except:
                                    pass
                                event_data = None
                                event_type = None
                            continue
                        if line.startswith("data:"):
                            event_data = line[5:].strip()
                        elif line.startswith("event:"):
                            event_type = line[6:].strip()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"SSE error: {e}")

    async def list_tools_sse(self):
        if not self.connected:
            raise ConnectionError("Not connected")
        return await self._send_request({"type": "list_tools"})

    async def call_tool_sse(self, tool_name: str, args: Dict[str, Any]):
        if not self.connected:
            raise ConnectionError("Not connected")
        return await self._send_request(
            {"type": "call_tool", "tool": tool_name, "arguments": args}
        )

    async def _send_request(self, request_data: Dict[str, Any]):
        if not self.connected or not self.session_id:
            raise ConnectionError("Not connected")
        request_data["session_id"] = self.session_id
        request_data["request_id"] = str(uuid.uuid4())
        base_url = self.address.rsplit("/sse", 1)[0]
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/messages", json=request_data
            ) as response:
                if response.status != 200:
                    raise ConnectionError(f"HTTP {response.status}")
                return await response.json()

    def _convert_tool_format(self, tool: Any) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            },
        }

    async def process_query(
        self,
        query: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
    ) -> str:
        if not self.connected:
            raise ConnectionError("Not connected to any MCP server")

        self.messages.append({"role": "user", "content": query})

        if tools is None:
            tools = self._tools or []

        if not tools:
            raise ValueError("No tools available")

        model_to_use = model or self.model
        if not model_to_use:
            raise ValueError("No model specified")

        response = self.openai.chat.completions.create(
            model=model_to_use,
            tools=tools,
            messages=self.messages,
            timeout=self.timeout,
        )

        message = response.choices[0].message
        self.messages.append(message.model_dump())

        if message.tool_calls:
            return await self._handle_tool_calls(message, model_to_use)
        return message.content or ""

    async def _handle_tool_calls(self, message: Any, model: str) -> str:
        results = []
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            try:
                if self.transport_type == "sse":
                    result = await self.call_tool_sse(tool_name, tool_args)
                else:
                    result = await self.session.call_tool(tool_name, tool_args)
                results.append(f"[{tool_name}] -> {result}")
                content = (
                    result.get("content", str(result))
                    if isinstance(result, dict)
                    else str(result)
                )
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": content,
                    }
                )
            except Exception as e:
                results.append(f"[{tool_name}] Error: {e}")

        response = self.openai.chat.completions.create(
            model=model, max_tokens=1000, messages=self.messages, timeout=self.timeout
        )
        results.append(response.choices[0].message.content or "")
        return "\n".join(results)

    def list_tools(self) -> List[Dict[str, Any]]:
        return self._tools or []

    async def cleanup(self):
        await self.disconnect()
        await self.exit_stack.aclose()
