"""
OpenRouter CLI - A command-line interface for OpenRouter's API.
"""

import os
import json
import asyncio
import pyperclip
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
from typing import List, Dict, Optional, Any
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from openrouter_cli.tools.openrouter_client import create_client
from openrouter_cli.tools.file_operations.ai_ops import AIPoweredFileOperations
from openrouter_cli.tools.mcp.mcp_client import MCPClient
from openrouter_cli.tools.mcp.mcp_manager import MCPServerManager
from openrouter_cli.schema_manager import SchemaManager
import shlex
import subprocess
import threading
from collections import deque

import logging

logging.getLogger("httpx").setLevel(logging.WARNING)  # Disable INFO logs

# Initialize Rich console
console = Console()

# Global state for MCP client and server
mcp_manager = MCPServerManager()
mcp_client_state = {
    "address": None,
    "connected": False,
    "session": None,
    "lock": asyncio.Lock(),
    "event_queue": asyncio.Queue(),
    "active_server": None,
}

mcp_server_state = {
    "running": False,
    "transport": "stdio",
    "port": 8000,
    "host": "0.0.0.0",
    "process": None,
    "address": None,
    "output_buffer": deque(maxlen=20),
    "output_thread": None,
}

slash_commands = [
    "/help",
    "/model",
    "/clear",
    "/copy",
    "/copy all",
    "/analyze",
    "/batch",
    "/clear-cache",
    "/update",
    "/mcp",
    "/mcp servers",
    "/mcp connect",
    "/mcp disconnect",
    "/mcp list",
    "/mcp use",
    "/mcp status",
    "/exit",
    "/quit",
]


class OpenRouterKeyManager:
    """Manages OpenRouter API keys."""

    def __init__(self):
        self.keys = []
        self.load_keys()

    def load_keys(self):
        """Load API keys from OPENROUTER_API_KEYS.json in home directory."""
        home_dir = Path.home()
        keys_file = home_dir / "OPENROUTER_API_KEYS.json"

        if keys_file.exists():
            try:
                with open(keys_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.keys = data
                    elif isinstance(data, dict) and "keys" in data:
                        self.keys = data["keys"]
                    else:
                        self.keys = []
                # console.print("[green]Successfully loaded API keys from OPENROUTER_API_KEYS.json[/green]")
            except Exception as e:
                console.print(f"[red]Error loading API keys: {str(e)}[/red]")
                self.keys = []
        else:
            console.print(
                "[yellow]No OPENROUTER_API_KEYS.json found in home directory[/yellow]"
            )
            self.keys = []

    def get_random_key(self) -> Optional[str]:
        """Get a random API key."""
        if not self.keys:
            return None
        # If keys is a list of strings, use first key
        if isinstance(self.keys[0], str):
            return self.keys[0]
        # If keys is a list of dicts with 'key' field
        elif isinstance(self.keys[0], dict) and "key" in self.keys[0]:
            return self.keys[0]["key"]
        return None

    def has_keys(self) -> bool:
        """Check if there are any API keys."""
        return len(self.keys) > 0


def load_models() -> List[Dict]:
    """Load models from YAML file."""
    try:
        with open("models.yaml", "r") as file:
            data = yaml.safe_load(file)
            return data.get("models", [])
    except Exception as e:
        console.print(f"[red]Error loading models: {str(e)}[/red]")
        return []


def display_models(models: List[Dict]) -> None:
    """Display available models in a table."""
    table = Table(title="Available Models")
    table.add_column("Index", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description", style="yellow")
    table.add_column("Category", style="blue")
    table.add_column("Max Tokens", style="magenta")
    table.add_column("Pricing", style="red")

    for idx, model in enumerate(models, 1):
        table.add_row(
            str(idx),
            model["name"],
            model["description"],
            model["category"],
            str(model["max_tokens"]),
            model["pricing"],
        )

    console.print(table)


def select_model(models: List[Dict]) -> str:
    """Let user select a model."""
    display_models(models)

    while True:
        try:
            choice = Prompt.ask("\nSelect a model (enter number)", default="1")
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                return models[idx]["name"]
            console.print("[red]Invalid selection. Please try again.[/red]")
        except ValueError:
            console.print("[red]Please enter a valid number.[/red]")


async def stream_chat(client, messages: List[Dict], model: Optional[str] = None):
    """Stream chat completion from OpenRouter."""
    try:
        # Add system message if not present
        if not any(msg["role"] == "system" for msg in messages):
            messages.insert(
                0,
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant. Please respond in English only.",
                },
            )

        response = await client.chat.completions.create(
            model=model or client.model, messages=messages, stream=True
        )

        full_response = ""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                console.print(content, end="", style="white")
                full_response += content

        console.print()  # New line after response
        return full_response

    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        return None


def format_chat_history(messages: List[Dict]) -> str:
    """Format chat history for clipboard."""
    formatted = []
    for msg in messages:
        role = "You" if msg["role"] == "user" else "Assistant"
        formatted.append(f"{role}: {msg['content']}\n")
    return "\n".join(formatted)


async def connect_sse_background(address):
    """Connect to MCP server using SSE transport."""
    try:
        async with mcp_client_state["lock"]:
            if mcp_client_state["connected"]:
                await disconnect_sse()

            # Create a client using the enhanced MCPClient from tools/file_operations
            # from tools.file_operations.mcp_client import MCPClient
            key_manager = OpenRouterKeyManager()
            api_key = key_manager.get_random_key()
            base_dir = str(Path.cwd())
            client = MCPClient(api_key=api_key, base_dir=base_dir)

            # Connect to the server using the SSE method
            if await client.connect(address):
                # Update state
                mcp_client_state["address"] = address
                mcp_client_state["connected"] = True
                mcp_client_state["session"] = client

                # Start background task for event processing
                async def process_events():
                    try:
                        while mcp_client_state["connected"]:
                            try:
                                # Get events from the client's queue
                                if not client._event_queue.empty():
                                    event = await client._event_queue.get()
                                    await mcp_client_state["event_queue"].put(event)
                                await asyncio.sleep(0.1)
                            except Exception as e:
                                console.print(
                                    f"[red]Error processing message: {str(e)}[/red]"
                                )
                                break
                    finally:
                        await disconnect_sse()

                # Start event processing in background
                asyncio.create_task(process_events())

                return True
            else:
                return False

    except Exception as e:
        console.print(f"[red]Failed to connect to MCP server: {str(e)}[/red]")
        await disconnect_sse()
        return False


async def disconnect_sse():
    """Disconnect from MCP server and clean up resources."""
    async with mcp_client_state["lock"]:
        if mcp_client_state["session"]:
            try:
                await mcp_client_state["session"].disconnect()
            except Exception as e:
                console.print(
                    f"[red]Error disconnecting from MCP server: {str(e)}[/red]"
                )
        mcp_client_state["address"] = None
        mcp_client_state["connected"] = False
        mcp_client_state["session"] = None


async def main():
    """Main function."""
    # Initialize key manager
    key_manager = OpenRouterKeyManager()
    key_manager.load_keys()

    # Make environment variable take precedence over OPENROUTER_API_KEYS.json
    current_api_key = os.getenv("OPENROUTER_API_KEY") or key_manager.get_random_key()

    if not current_api_key:
        console.print(
            "[red]No API keys found. Please add your OpenRouter API key.[/red]"
        )
        return

    # Create client
    client = create_client(current_api_key)

    # Load models
    models = load_models()
    if not models:
        console.print("[red]No models found. Please check your models.yaml file.[/red]")
        return

    # Select initial model
    selected_model = select_model(models)
    if not selected_model:
        console.print("[red]No model selected. Exiting.[/red]")
        return

    # Initialize schema manager
    schema_manager = SchemaManager()
    schema_manager.use_schema("chat")  # Use default chat schema

    # Initialize file operations
    file_ops = AIPoweredFileOperations(
        base_dir=".", api_key=key_manager.get_random_key()
    )

    # Start chat session
    console.print(
        Panel.fit(
            f"[bold blue]OpenRouter Chat[/bold blue]\n"
            f"Selected Model: [green]{selected_model}[/green]\n\n"
            "[bold]Available Commands:[/bold]\n"
            "  /model - Switch model\n"
            "  /clear - Clear chat history\n"
            "  /copy - Copy last response\n"
            "  /copy all - Copy entire conversation\n"
            "  /analyze <file> - Analyze a file\n"
            "  /batch <pattern> - Batch analyze files\n"
            "  /clear-cache - Clear analysis cache\n"
            "  /update - Update free models from OpenRouter\n"
            "  /mcp servers - List MCP servers\n"
            "  /mcp connect <name> - Connect to MCP server\n"
            "  /mcp disconnect - Disconnect from server\n"
            "  /mcp list - List MCP tools\n"
            "  /mcp use <tool> --arg=value - Use MCP tool\n"
            "  /mcp status - Show MCP status\n"
            "  /help - Show this help message\n"
            "  /exit or /quit - Exit the application\n\n"
            "[dim]Type / for commands, ! for system commands[/dim]\n"
            "Type your message to start chatting...\n"
            "Use ! prefix to run system commands (e.g., !dir)",
            title="Welcome",
            border_style="blue",
        )
    )

    messages = []

    def _read_server_output(proc, buffer):
        try:
            for line in iter(proc.stdout.readline, ""):
                if not line:
                    break
                print(f"[MCP Server] {line.rstrip()}")
                buffer.append(line.rstrip())
        except Exception as e:
            buffer.append(f"[output error] {e}")

    while True:
        # Get user input
        user_input = Prompt.ask("\n[bold green]You[/bold green]")

        # Handle commands
        if user_input.lower() in ["exit", "quit", "/exit", "/quit"]:
            if mcp_server_state["process"] is not None:
                mcp_server_state["process"].terminate()
                mcp_server_state["process"] = None
                mcp_server_state["running"] = False
                mcp_server_state["output_thread"] = None
                console.print("[yellow]MCP server stopped[/yellow]")
            await disconnect_sse()
            break
        elif user_input.startswith("!"):
            # Execute system command
            try:
                result = subprocess.run(
                    user_input[1:], shell=True, capture_output=True, text=True
                )
                if result.stdout:
                    console.print(result.stdout)
                if result.stderr:
                    console.print(f"[red]{result.stderr}[/red]")
            except Exception as e:
                console.print(f"[red]Error executing command: {str(e)}[/red]")
            continue  # Do NOT send to LLM or add to history
        elif user_input.startswith("/"):
            # Handle all slash commands here (do NOT send to LLM or add to history)
            if user_input == "/model":
                # Load and select new model
                models = load_models()
                if models:
                    selected_model = select_model(models)
                    console.print(f"[green]Switched to model: {selected_model}[/green]")
                else:
                    console.print("[red]No models available[/red]")

            elif user_input == "/clear":
                messages = []
                console.print("[yellow]Chat history cleared[/yellow]")

            elif user_input == "/copy":
                if messages and messages[-1]["role"] == "assistant":
                    pyperclip.copy(messages[-1]["content"])
                    console.print("[green]Copied last response to clipboard![/green]")
                else:
                    console.print("[yellow]No response to copy[/yellow]")

            elif user_input == "/copy all":
                if messages:
                    formatted_history = format_chat_history(messages)
                    pyperclip.copy(formatted_history)
                    console.print(
                        "[green]Copied entire conversation to clipboard![/green]"
                    )
                else:
                    console.print("[yellow]No conversation to copy[/yellow]")

            elif user_input.startswith("/analyze "):
                file_path = user_input[9:].strip()
                if os.path.exists(file_path):
                    console.print(f"\n[blue]Analyzing file: {file_path}[/blue]")
                    try:
                        result = await file_ops.analyze_file(
                            file_path,
                            "Analyze this file and provide a detailed summary",
                        )
                        console.print("\n[bold]Analysis Results:[/bold]")
                        console.print("-" * 50)
                        console.print(result["analysis"])
                        console.print("-" * 50)
                        console.print(f"\nModel used: {result['model']}")
                        console.print(
                            f"Processing time: {result['processing_time']:.2f} seconds"
                        )
                        console.print(f"Cache hit: {result['cache_hit']}")
                    except Exception as e:
                        console.print(f"[red]Error analyzing file: {str(e)}[/red]")
                else:
                    console.print("[red]File not found[/red]")

            elif user_input.startswith("/batch "):
                pattern = user_input[7:].strip()
                console.print(
                    f"\n[blue]Analyzing files matching pattern: {pattern}[/blue]"
                )
                try:
                    results = await file_ops.batch_analyze_files(
                        [str(f) for f in Path(".").glob(pattern)],
                        "Compare these files and identify common themes",
                    )
                    console.print("\n[bold]Batch Analysis Results:[/bold]")
                    console.print("-" * 50)
                    for file_path, result in results.items():
                        console.print(f"\n[bold]File: {file_path}[/bold]")
                        console.print("-" * 30)
                        console.print(result["analysis"])
                        console.print(
                            f"Processing time: {result['processing_time']:.2f} seconds"
                        )
                        console.print(f"Cache hit: {result['cache_hit']}")
                except Exception as e:
                    console.print(f"[red]Error analyzing files: {str(e)}[/red]")

            elif user_input == "/clear-cache":
                if await file_ops.clear_cache():
                    console.print("[green]Cache cleared[/green]")
                else:
                    console.print("[red]Error clearing cache[/red]")

            elif user_input == "/mcp servers":
                servers = mcp_manager.list_servers()
                if not servers:
                    console.print(
                        "[yellow]No MCP servers configured. Copy mcp_servers.json.example to mcp_servers.json[/yellow]"
                    )
                else:
                    table = Table(title="Configured MCP Servers")
                    table.add_column("Name", style="green")
                    table.add_column("Type", style="cyan")
                    table.add_column("URL/Command", style="yellow")
                    table.add_column("Status", style="magenta")
                    for s in servers:
                        status = (
                            "[green]Active[/green]"
                            if s["active"]
                            else "[red]Inactive[/red]"
                        )
                        table.add_row(
                            s["name"],
                            s["type"],
                            s["url"][:50] + "..." if len(s["url"]) > 50 else s["url"],
                            status,
                        )
                    console.print(table)
                continue

            elif user_input.startswith("/mcp connect "):
                server_name = user_input[len("/mcp connect ") :].strip()
                if not server_name:
                    console.print("[yellow]Usage: /mcp connect <server_name>[/yellow]")
                    continue

                config = mcp_manager.get_server_config(server_name)
                if not config:
                    console.print(
                        f"[red]Server '{server_name}' not found in config[/red]"
                    )
                    continue

                if mcp_client_state["session"]:
                    await mcp_client_state["session"].cleanup()

                client = MCPClient(
                    api_key=current_api_key, base_dir=".", model=selected_model
                )
                success = await mcp_manager.connect(server_name, client)
                if success:
                    mcp_client_state["session"] = client
                    mcp_client_state["connected"] = True
                    mcp_client_state["active_server"] = server_name
                    console.print(
                        f"[green]Connected to MCP server '{server_name}'[/green]"
                    )
                else:
                    console.print(f"[red]Failed to connect to '{server_name}'[/red]")
                continue

            elif user_input == "/mcp disconnect":
                if mcp_client_state["session"]:
                    await mcp_client_state["session"].cleanup()
                    mcp_client_state["session"] = None
                    mcp_client_state["connected"] = False
                    mcp_client_state["active_server"] = None
                    console.print("[green]Disconnected from MCP server[/green]")
                else:
                    console.print("[yellow]Not connected to any MCP server[/yellow]")
                continue

            elif user_input == "/mcp list":
                if not mcp_client_state["connected"] or not mcp_client_state["session"]:
                    console.print(
                        "[yellow]Not connected to any MCP server. Use /mcp connect <name>[/yellow]"
                    )
                    continue
                try:
                    tools = mcp_client_state["session"].list_tools()
                    if tools:
                        table = Table(
                            title=f"MCP Tools ({mcp_client_state['active_server']})"
                        )
                        table.add_column("Name", style="green")
                        table.add_column("Description", style="yellow")
                        for tool in tools:
                            name = tool.get("function", {}).get("name", "unknown")
                            desc = tool.get("function", {}).get("description", "")[:60]
                            table.add_row(name, desc)
                        console.print(table)
                    else:
                        console.print("[yellow]No tools available[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error: {str(e)}[/red]")
                continue

            elif user_input.startswith("/mcp use "):
                parts = user_input[9:].strip().split("--")
                tool_name = parts[0].strip()
                args = {}
                for part in parts[1:]:
                    if "=" in part:
                        key, value = part.split("=", 1)
                        args[key.strip()] = value.strip()
                    else:
                        args[part.strip()] = True

                if not mcp_client_state["connected"] or not mcp_client_state["session"]:
                    console.print(
                        "[yellow]Not connected. Use /mcp connect <name> first[/yellow]"
                    )
                    continue

                try:
                    result = await mcp_client_state["session"].process_query(
                        f"Use the {tool_name} tool with these parameters: {json.dumps(args)}",
                        model=selected_model,
                    )
                    console.print(
                        Panel.fit(
                            result,
                            title=f"[green]{tool_name}[/green]",
                            border_style="blue",
                        )
                    )
                except Exception as e:
                    console.print(f"[red]Error: {str(e)}[/red]")
                continue

            elif user_input == "/mcp status":
                if mcp_client_state["connected"] and mcp_client_state["session"]:
                    client = mcp_client_state["session"]
                    console.print(
                        Panel.fit(
                            f"Status: [green]Connected[/green]\n"
                            f"Server: [cyan]{mcp_client_state.get('active_server', 'unknown')}[/cyan]\n"
                            f"Transport: [yellow]{getattr(client, 'transport_type', 'unknown')}[/yellow]\n"
                            f"Tools: [cyan]{len(client.list_tools())}[/cyan]",
                            title="MCP Status",
                            border_style="blue",
                        )
                    )
                else:
                    console.print(
                        Panel.fit(
                            "Status: [red]Disconnected[/red]\n"
                            "Use /mcp servers to see available servers\n"
                            "Use /mcp connect <name> to connect",
                            title="MCP Status",
                            border_style="blue",
                        )
                    )
                continue

            elif user_input.startswith("/mcp server start"):
                args = shlex.split(user_input[len("/mcp server start") :].strip())
                transport = "stdio"
                port = 8000
                host = "0.0.0.0"
                i = 0
                while i < len(args):
                    if args[i] == "--transport" and i + 1 < len(args):
                        transport = args[i + 1]
                        i += 2
                    elif args[i] == "--port" and i + 1 < len(args):
                        port = int(args[i + 1])
                        i += 2
                    elif args[i] == "--host" and i + 1 < len(args):
                        host = args[i + 1]
                        i += 2
                    else:
                        i += 1
                if (
                    mcp_server_state["process"] is None
                    or not mcp_server_state["running"]
                ):
                    try:
                        cmd = [
                            "python",
                            "tools/mcp_server.py",
                            "--transport",
                            transport,
                            "--port",
                            str(port),
                            "--host",
                            host,
                        ]
                        proc = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1,
                        )
                        mcp_server_state["process"] = proc
                        mcp_server_state["running"] = True
                        mcp_server_state["transport"] = transport
                        mcp_server_state["port"] = port
                        mcp_server_state["host"] = host
                        mcp_server_state["address"] = (
                            f"http://{host if host != '0.0.0.0' else 'localhost'}:{port}/sse"
                            if transport == "sse"
                            else None
                        )
                        mcp_server_state["output_buffer"].clear()
                        # Start output reader thread
                        t = threading.Thread(
                            target=_read_server_output,
                            args=(proc, mcp_server_state["output_buffer"]),
                            daemon=True,
                        )
                        t.start()
                        mcp_server_state["output_thread"] = t
                        console.print(
                            f"[green]MCP server started with transport={transport}, port={port}, host={host}[/green]"
                        )
                        if mcp_server_state["address"]:
                            console.print(
                                f"[blue]Server address: {mcp_server_state['address']}[/blue]"
                            )
                    except Exception as e:
                        console.print(f"[red]Error starting MCP server: {str(e)}[/red]")
                else:
                    console.print("[yellow]MCP server is already running[/yellow]")
                continue

            elif user_input == "/update":
                console.print(
                    "[yellow]Checking for free models on OpenRouter...[/yellow]"
                )
                try:
                    import openai

                    update_client = openai.OpenAI(
                        api_key=current_api_key, base_url="https://openrouter.ai/api/v1"
                    )
                    models_data = update_client.models.list()

                    free_models = []
                    for m in models_data.data:
                        if ":free" in m.id.lower():
                            free_models.append(
                                {
                                    "name": m.id,
                                    "description": m.id.split("/")[-1]
                                    .replace("-", " ")
                                    .replace("_", " ")
                                    .title(),
                                    "category": m.id.split("/")[0].title(),
                                    "max_tokens": 131072,
                                    "pricing": "Free",
                                    "features": ["Free tier", "OpenRouter"],
                                }
                            )

                    if not free_models:
                        console.print("[yellow]No free models found[/yellow]")
                    else:
                        yaml_content = "models:\n\n"
                        for model in free_models:
                            yaml_content += f'  - name: "{model["name"]}"\n'
                            yaml_content += (
                                f'    description: "{model["description"]}"\n'
                            )
                            yaml_content += f'    category: "{model["category"]}"\n'
                            yaml_content += f"    max_tokens: {model['max_tokens']}\n"
                            yaml_content += f'    pricing: "{model["pricing"]}"\n'
                            yaml_content += "    features:\n"
                            for feature in model["features"]:
                                yaml_content += f'      - "{feature}"\n'
                            yaml_content += "\n"

                        with open("models.yaml", "w") as f:
                            f.write(yaml_content)

                        console.print(
                            f"[green]Updated models.yaml with {len(free_models)} free models![/green]"
                        )
                        console.print(
                            "[blue]Restart the app to see updated model list (/model)[/blue]"
                        )
                except Exception as e:
                    console.print(f"[red]Error updating models: {str(e)}[/red]")
                continue

            elif user_input == "/help":
                console.print(
                    Panel.fit(
                        "[bold]Available Commands:[/bold]\n"
                        "  /model - Switch model\n"
                        "  /clear - Clear chat history\n"
                        "  /copy - Copy last response\n"
                        "  /copy all - Copy entire conversation\n"
                        "  /analyze <file> - Analyze a file\n"
                        "  /batch <pattern> - Batch analyze files\n"
                        "  /clear-cache - Clear analysis cache\n"
                        "  /update - Update free models from OpenRouter\n"
                        "  /mcp servers - List configured MCP servers\n"
                        "  /mcp connect <name> - Connect to an MCP server\n"
                        "  /mcp disconnect - Disconnect from MCP server\n"
                        "  /mcp list - List available MCP tools\n"
                        "  /mcp use <tool> --arg=value - Use an MCP tool\n"
                        "  /mcp status - Show MCP connection status\n"
                        "  /help - Show this help message\n"
                        "  /exit or /quit - Exit the application\n\n"
                        "Use ! prefix to run system commands (e.g., !dir)",
                        title="Help",
                        border_style="blue",
                    )
                )
                continue

            continue

        elif user_input.strip() == "":
            continue

        # Only add to history and send to LLM if not a command
        messages.append({"role": "user", "content": user_input})

        # Get response from OpenRouter
        response = await stream_chat(client, messages, selected_model)
        if response:
            messages.append({"role": "assistant", "content": response})

            # Validate response against schema
            is_valid, errors = schema_manager.validate_response(response)
            if not is_valid:
                console.print(
                    f"\n[yellow]Warning: Response validation failed: {errors}[/yellow]"
                )


if __name__ == "__main__":
    asyncio.run(main())
