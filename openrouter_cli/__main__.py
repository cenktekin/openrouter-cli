"""
Entry point for running the OpenRouter CLI as a module.
"""

import asyncio
from openrouter_cli.main import main

if __name__ == "__main__":
    asyncio.run(main())