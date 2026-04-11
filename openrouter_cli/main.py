"""OpenRouter CLI - Minimal chat interface."""

import os
import sys
import json
import asyncio
import pyperclip
import yaml
from pathlib import Path
from dotenv import load_dotenv

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from openrouter_cli.openrouter_client import OpenRouterClient
from openrouter_cli.key_manager import OpenRouterKeyManager

load_dotenv()

console = Console()

COMMANDS = {
    "/help": "Show help message",
    "/model": "Switch model",
    "/clear": "Clear chat history",
    "/copy": "Copy last response",
    "/copy all": "Copy entire conversation",
    "/settings": "Show model settings",
    "/temperature": "Set temperature (0-2)",
    "/top_p": "Set top P (0-1)",
    "/max_tokens": "Set max tokens (100-32000)",
    "/update": "Update free models from OpenRouter",
    "/exit": "Exit the application",
}

# Model settings
model_settings = {
    "temperature": 0.7,
    "top_p": 1.0,
    "max_tokens": 4096,
}


def load_models() -> list:
    """Load models from YAML file."""
    try:
        with open("models.yaml", "r") as f:
            data = yaml.safe_load(f)
            return data.get("models", [])
    except Exception as e:
        console.print(f"[red]Error loading models: {e}[/red]")
        return []


def display_models(models: list) -> None:
    """Display available models."""
    table = Table(title="Available Models")
    table.add_column("#", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Context", style="yellow")
    table.add_column("Category", style="blue")
    table.add_column("Pricing", style="red")

    for idx, model in enumerate(models, 1):
        context = model.get("context_length", model.get("max_tokens", "-"))
        if isinstance(context, int):
            context = f"{context:,}"
        table.add_row(
            str(idx),
            model["name"],
            str(context),
            model["category"],
            model["pricing"],
        )

    console.print(table)


def select_model(models: list) -> str:
    """Let user select a model by number."""
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


async def stream_chat(client: OpenRouterClient, messages: list, model: str) -> str:
    """Stream chat completion."""
    try:
        response = client.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=model_settings["temperature"],
            top_p=model_settings["top_p"],
            max_tokens=model_settings["max_tokens"],
        )

        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                console.print(content, end="", style="white")
                full_response += content

        console.print()
        return full_response

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        return None


def format_chat_history(messages: list) -> str:
    """Format chat history for clipboard."""
    formatted = []
    for msg in messages:
        role = "You" if msg["role"] == "user" else "Assistant"
        formatted.append(f"{role}: {msg['content']}\n")
    return "\n".join(formatted)


async def update_models(api_key: str) -> None:
    """Update free models from OpenRouter."""
    console.print("[yellow]Fetching free models from OpenRouter...[/yellow]")
    try:
        client = OpenRouterClient(api_key)
        models_data = client.client.models.list()

        free_models = []
        for m in models_data.data:
            # Include models that are :free or have 'free' in their ID
            if m.id.endswith(":free") or (m.id.startswith("openrouter/") and "free" in m.id.lower()):
                free_models.append(
                    {
                        "name": m.id,
                        "description": m.id.split("/")[-1].replace("-", " ").replace(
                            "_", " "
                        ).title(),
                        "category": m.id.split("/")[0].title(),
                        "context_length": getattr(m, "context_length", 131072),
                        "created": getattr(m, "created", 0),  # Unix timestamp
                        "max_tokens": 131072,
                        "pricing": "Free",
                        "features": ["Free tier", "OpenRouter"],
                    }
                )

        # Sort by created timestamp (newest first)
        free_models.sort(key=lambda x: -x["created"])

        if not free_models:
            console.print("[yellow]No free models found.[/yellow]")
            return

        yaml_content = "models:\n\n"
        for model in free_models:
            yaml_content += f'  - name: "{model["name"]}"\n'
            yaml_content += f'    description: "{model["description"]}"\n'
            yaml_content += f'    category: "{model["category"]}"\n'
            yaml_content += f"    context_length: {model['context_length']}\n"
            yaml_content += f"    max_tokens: {model['max_tokens']}\n"
            yaml_content += f'    pricing: "{model["pricing"]}"\n'
            yaml_content += "    features:\n"
            for feature in model["features"]:
                yaml_content += f'      - "{feature}"\n'
            yaml_content += "\n"

        with open("models.yaml", "w") as f:
            f.write(yaml_content)

        console.print(f"[green]Updated models.yaml with {len(free_models)} models![/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


async def main():
    """Main entry point."""
    key_manager = OpenRouterKeyManager()
    key_manager.load_keys()

    api_key = os.getenv("OPENROUTER_API_KEY") or key_manager.get_random_key()

    if not api_key:
        console.print("[red]No API key found. Set OPENROUTER_API_KEY or add keys to OPENROUTER_API_KEYS.json.[/red]")
        sys.exit(1)

    client = OpenRouterClient(api_key)

    models = load_models()
    if not models:
        console.print("[yellow]No models found. Fetching free models from OpenRouter...[/yellow]")
        await update_models(api_key)
        models = load_models()
        if not models:
            console.print("[red]Still no models. Check your API key.[/red]")
            sys.exit(1)

    selected_model = select_model(models)

    console.print(
        Panel.fit(
            f"[bold blue]OpenRouter CLI[/bold blue]\n"
            f"Model: [green]{selected_model}[/green]\n\n"
            f"[bold]Commands:[/bold]\n"
            "  /help - Show help\n"
            "  /model - Switch model\n"
            "  /clear - Clear history\n"
            "  /copy - Copy last response\n"
            "  /copy all - Copy all\n"
            "  /settings - Show model settings\n"
            "  /temperature <0-2> - Set temperature\n"
            "  /top_p <0-1> - Set top P\n"
            "  /max_tokens <100-32000> - Set max tokens\n"
            "  /update - Update models\n"
            "  /exit - Exit\n",
            title="Welcome",
            border_style="blue",
        )
    )

    messages = []

    while True:
        try:
            user_input = Prompt.ask("\nYou")
        except KeyboardInterrupt:
            console.print("\n[yellow]Press Ctrl+C again to exit, or type /exit[/yellow]")
            try:
                user_input = Prompt.ask("\nYou")
            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye![/yellow]")
                break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "/exit", "/quit"]:
            console.print("[yellow]Goodbye![/yellow]")
            break

        if user_input.startswith("/"):
            if user_input == "/help":
                console.print(
                    Panel.fit(
                        "\n".join(f"  {cmd} - {desc}" for cmd, desc in COMMANDS.items()),
                        title="Commands",
                        border_style="blue",
                    )
                )
                continue

            elif user_input == "/model":
                models = load_models()
                if models:
                    selected_model = select_model(models)
                    console.print(f"[green]Switched to: {selected_model}[/green]")
                else:
                    console.print("[red]No models available.[/red]")
                continue

            elif user_input == "/clear":
                messages = []
                console.print("[yellow]History cleared.[/yellow]")
                continue

            elif user_input == "/copy":
                if messages and messages[-1]["role"] == "assistant":
                    pyperclip.copy(messages[-1]["content"])
                    console.print("[green]Copied last response.[/green]")
                else:
                    console.print("[yellow]No response to copy.[/yellow]")
                continue

            elif user_input == "/copy all":
                if messages:
                    pyperclip.copy(format_chat_history(messages))
                    console.print("[green]Copied conversation.[/green]")
                else:
                    console.print("[yellow]Nothing to copy.[/yellow]")
                continue

            elif user_input == "/settings":
                console.print(
                    Panel.fit(
                        f"[bold]Temperature:[/bold] {model_settings['temperature']}\n"
                        f"[bold]Top P:[/bold] {model_settings['top_p']}\n"
                        f"[bold]Max Tokens:[/bold] {model_settings['max_tokens']}\n\n"
                        f"[dim]Usage: /temperature <0-2>, /top_p <0-1>, /max_tokens <100-32000>[/dim]",
                        title="Model Settings",
                        border_style="blue",
                    )
                )
                continue

            elif user_input.startswith("/temperature "):
                try:
                    value = float(user_input.split()[1])
                    if 0.0 <= value <= 2.0:
                        model_settings["temperature"] = value
                        console.print(f"[green]Temperature set to {value}[/green]")
                    else:
                        console.print("[yellow]Temperature must be between 0.0 and 2.0[/yellow]")
                except (ValueError, IndexError):
                    console.print("[yellow]Usage: /temperature <0.0-2.0>[/yellow]")
                continue

            elif user_input.startswith("/top_p "):
                try:
                    value = float(user_input.split()[1])
                    if 0.0 <= value <= 1.0:
                        model_settings["top_p"] = value
                        console.print(f"[green]Top P set to {value}[/green]")
                    else:
                        console.print("[yellow]Top P must be between 0.0 and 1.0[/yellow]")
                except (ValueError, IndexError):
                    console.print("[yellow]Usage: /top_p <0.0-1.0>[/yellow]")
                continue

            elif user_input.startswith("/max_tokens "):
                try:
                    value = int(user_input.split()[1])
                    if 100 <= value <= 32000:
                        model_settings["max_tokens"] = value
                        console.print(f"[green]Max tokens set to {value}[/green]")
                    else:
                        console.print("[yellow]Max tokens must be between 100 and 32000[/yellow]")
                except (ValueError, IndexError):
                    console.print("[yellow]Usage: /max_tokens <100-32000>[/yellow]")
                continue

            elif user_input == "/update":
                await update_models(api_key)
                continue

            else:
                console.print(f"[yellow]Unknown command: {user_input}[/yellow]")
                console.print("Type /help for available commands.")
                continue

        if not user_input.strip():
            continue

        messages.append({"role": "user", "content": user_input})

        response = await stream_chat(client, messages, selected_model)

        if response:
            messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
