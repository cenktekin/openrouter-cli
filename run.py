#!/usr/bin/env python3
"""
Run script for OpenRouter CLI.
"""

import asyncio
from openrouter_cli.main import main

if __name__ == "__main__":
    asyncio.run(main())
