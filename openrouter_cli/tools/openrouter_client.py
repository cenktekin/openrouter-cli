"""
OpenRouter client functionality.
"""

import os
from typing import Optional
from openai import AsyncOpenAI

# import logging
# logging.getLogger("httpx").setLevel(logging.WARNING)  # Disable INFO logs


def create_client(api_key: Optional[str] = None) -> AsyncOpenAI:
    """Create an OpenRouter client."""
    # Get API key from environment or parameter
    key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise ValueError(
            "OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable or provide api_key parameter."
        )

    # Create client
    client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1/", api_key=key)

    return client
