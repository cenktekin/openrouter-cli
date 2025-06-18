#!/usr/bin/env python3
"""
Example script demonstrating the usage of MCP file operations.
"""

import asyncio
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

from tools.file_operations.mcp_ops import MCPFileOperations

# Initialize console
console = Console()

async def main():
    """Main function demonstrating MCP file operations."""

    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        console.print("[red]Error: OPENROUTER_API_KEY environment variable not set[/red]")
        return

    # Initialize MCP file operations
    base_dir = Path(__file__).parent.parent
    mcp_ops = MCPFileOperations(
        base_dir=str(base_dir),
        api_key=api_key,
        allowed_extensions=[".txt", ".md", ".py", ".pdf", ".jpg", ".jpeg", ".png"],
        max_file_size=10 * 1024 * 1024,  # 10MB
        cache_dir=".cache"
    )

    try:
        # Example 1: Analyze a single file
        console.print(Panel.fit("Example 1: Analyzing a single file"))
        file_path = base_dir / "README.md"
        if file_path.exists():
            result = await mcp_ops.analyze_file(
                file_path,
                "Summarize the main points of this document."
            )
            console.print(result)

        # Example 2: Batch analyze multiple files
        console.print(Panel.fit("Example 2: Batch analyzing multiple files"))
        files_to_analyze = [
            base_dir / "README.md",
            base_dir / "requirements.txt",
            base_dir / "setup.py"
        ]

        with Progress() as progress:
            task = progress.add_task("Analyzing files...", total=len(files_to_analyze))

            async def process_with_progress(file_path: Path):
                result = await mcp_ops.analyze_file(
                    file_path,
                    "What is the purpose of this file?"
                )
                progress.update(task, advance=1)
                return result

            results = await asyncio.gather(
                *[process_with_progress(f) for f in files_to_analyze if f.exists()]
            )

        for result in results:
            console.print(result)

        # Example 3: Clear cache
        console.print(Panel.fit("Example 3: Clearing cache"))
        await mcp_ops.clear_cache()
        console.print("[green]Cache cleared successfully[/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

    finally:
        # Cleanup
        await mcp_ops.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
