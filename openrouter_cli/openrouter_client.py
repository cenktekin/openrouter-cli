"""Simple OpenRouter client."""

import os
from openai import OpenAI


class OpenRouterClient:
    """Minimal OpenRouter API client."""

    def __init__(self, api_key: str):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    def list_models(self):
        """List available models."""
        response = self.client.models.list()
        return [model.id for model in response.data]

    def chat(self, messages: list, model: str) -> str:
        """Send chat completion request."""
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return response.choices[0].message.content
