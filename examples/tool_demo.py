import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from dotenv import load_dotenv
from tools.web_search import WebSearchTool
from tools.image_generation import ImageGenerationTool
from tools.code_execution import CodeExecutionTool

# Load environment variables
load_dotenv()

console = Console()

def main():
    """Demonstrate tool usage."""
    # Initialize tools
    web_search = WebSearchTool()
    image_gen = ImageGenerationTool()
    code_exec = CodeExecutionTool()

    console.print(Panel.fit(
        "[bold blue]OpenRouter Tool Demo[/bold blue]\n\n"
        "Available tools:\n"
        "1. Web Search\n"
        "2. Image Generation\n"
        "3. Code Execution\n\n"
        "Type 'exit' to quit",
        title="Welcome"
    ))

    while True:
        # Get user input
        user_input = Prompt.ask("\n[bold green]Select a tool[/bold green] (1-3)")

        if user_input.lower() == 'exit':
            break

        try:
            tool_choice = int(user_input)
        except ValueError:
            console.print("[red]Please enter a number between 1 and 3[/red]")
            continue

        if tool_choice == 1:
            # Web Search
            query = Prompt.ask("[cyan]Enter search query[/cyan]")
            console.print("[yellow]Searching...[/yellow]")

            results = web_search.search(query)
            if "error" in results:
                console.print(f"[red]Error: {results['error']}[/red]")
            else:
                console.print("\n[bold]Search Results:[/bold]")
                for result in results["results"]:
                    console.print(f"\n[bold]{result['title']}[/bold]")
                    console.print(f"[link={result['url']}]{result['url']}[/link]")
                    console.print(result['snippet'])

        elif tool_choice == 2:
            # Image Generation
            prompt = Prompt.ask("[cyan]Enter image prompt[/cyan]")
            size = Prompt.ask("[cyan]Enter image size[/cyan]", default="1024x1024")
            num_images = int(Prompt.ask("[cyan]Number of images[/cyan]", default="1"))

            console.print("[yellow]Generating image...[/yellow]")
            result = image_gen.generate(prompt, size, num_images)

            if "error" in result:
                console.print(f"[red]Error: {result['error']}[/red]")
            else:
                console.print("\n[bold]Generated Images:[/bold]")
                for path in result["image_paths"]:
                    console.print(f"Saved to: {path}")

        elif tool_choice == 3:
            # Code Execution
            language = Prompt.ask("[cyan]Enter programming language[/cyan]", default="python")
            code = Prompt.ask("[cyan]Enter code[/cyan]")

            console.print("[yellow]Executing code...[/yellow]")
            result = code_exec.execute(code, language)

            if "error" in result:
                console.print(f"[red]Error: {result['error']}[/red]")
            else:
                console.print("\n[bold]Execution Result:[/bold]")
                console.print(f"Exit Code: {result['exit_code']}")
                console.print("\nOutput:")
                console.print(result["output"])
                if result.get("truncated"):
                    console.print("[yellow]Output was truncated[/yellow]")

        else:
            console.print("[red]Invalid tool choice. Please select 1-3.[/red]")

if __name__ == "__main__":
    main()
