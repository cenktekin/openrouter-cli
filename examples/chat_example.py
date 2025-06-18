#!/usr/bin/env python3
"""
Example script demonstrating chat functionality with OpenRouter CLI.
"""

import asyncio
from openrouter_cli import OpenRouterKeyManager, create_client
from schema_manager import SchemaManager

async def main():
    # Initialize key manager
    key_manager = OpenRouterKeyManager()
    if not key_manager.has_keys():
        print("No API keys found. Please set up your API keys first.")
        return

    # Create OpenRouter client
    client = create_client(api_key=key_manager.get_random_key())

    # Initialize schema manager
    schema_manager = SchemaManager()
    schema_manager.use_schema("chat")  # Use default chat schema

    # Start chat session
    print("Starting chat session (type 'exit' to quit)")
    print("Available commands:")
    print("  /model - Switch model")
    print("  /clear - Clear chat history")
    print("  /copy - Copy last response")
    print("  /help - Show this help message")

    messages = []
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()

        # Handle commands
        if user_input.lower() == 'exit':
            break
        elif user_input.startswith('/'):
            if user_input == '/model':
                # List available models
                print("\nAvailable models:")
                models = [
                    "openai/gpt-4",
                    "anthropic/claude-3-opus-20240229",
                    "google/gemini-pro"
                ]
                for i, model in enumerate(models, 1):
                    print(f"{i}. {model}")

                # Get model selection
                try:
                    choice = int(input("\nSelect model (1-3): "))
                    if 1 <= choice <= len(models):
                        client.model = models[choice - 1]
                        print(f"Switched to model: {client.model}")
                    else:
                        print("Invalid selection")
                except ValueError:
                    print("Please enter a number")

            elif user_input == '/clear':
                messages = []
                print("Chat history cleared")

            elif user_input == '/copy':
                if messages and messages[-1]["role"] == "assistant":
                    print(f"\nCopied to clipboard: {messages[-1]['content']}")
                else:
                    print("No response to copy")

            elif user_input == '/help':
                print("\nAvailable commands:")
                print("  /model - Switch model")
                print("  /clear - Clear chat history")
                print("  /copy - Copy last response")
                print("  /help - Show this help message")

            continue

        # Add user message to history
        messages.append({"role": "user", "content": user_input})

        try:
            # Get response from OpenRouter
            response = await client.chat.completions.create(
                model=client.model,
                messages=messages,
                stream=True
            )

            # Process streaming response
            print("\nAssistant: ", end="", flush=True)
            full_response = ""
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content

            print()  # New line after response

            # Add assistant response to history
            messages.append({"role": "assistant", "content": full_response})

            # Validate response against schema
            is_valid, errors = schema_manager.validate_response(full_response)
            if not is_valid:
                print(f"\nWarning: Response validation failed: {errors}")

        except Exception as e:
            print(f"\nError: {str(e)}")
            # Try to rotate API key on error
            new_key = key_manager.get_random_key()
            if new_key:
                client = create_client(api_key=new_key)
                print("Rotated to new API key")

if __name__ == "__main__":
    asyncio.run(main())
