#!/usr/bin/env python3
"""
Example script demonstrating schema management functionality with OpenRouter CLI.
"""

import asyncio
import json
from openrouter_cli import OpenRouterKeyManager, create_client
from schema_manager import SchemaManager

# Define example schemas
SCHEMAS = {
    "code_review": {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["bug", "security", "style", "performance"]},
                        "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                        "description": {"type": "string"},
                        "line": {"type": "integer"},
                        "suggestion": {"type": "string"}
                    },
                    "required": ["type", "severity", "description"]
                }
            },
            "suggestions": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["summary", "issues"]
    },

    "document_summary": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "key_points": {
                "type": "array",
                "items": {"type": "string"}
            },
            "topics": {
                "type": "array",
                "items": {"type": "string"}
            },
            "sentiment": {
                "type": "object",
                "properties": {
                    "overall": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["overall", "confidence"]
            }
        },
        "required": ["title", "summary", "key_points"]
    },

    "image_analysis": {
        "type": "object",
        "properties": {
            "description": {"type": "string"},
            "objects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "location": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "number"},
                                "y": {"type": "number"},
                                "width": {"type": "number"},
                                "height": {"type": "number"}
                            }
                        }
                    },
                    "required": ["name", "confidence"]
                }
            },
            "colors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "color": {"type": "string"},
                        "percentage": {"type": "number", "minimum": 0, "maximum": 100}
                    },
                    "required": ["color", "percentage"]
                }
            }
        },
        "required": ["description", "objects"]
    }
}

async def test_schema(schema_manager: SchemaManager, client, schema_name: str):
    """Test a schema with example prompts."""
    print(f"\nTesting schema: {schema_name}")
    print("-" * 50)

    # Use the schema
    schema_manager.use_schema(schema_name)
    print(f"Using schema: {schema_name}")

    # Get schema details
    schema = schema_manager.get_current_schema()
    print("\nSchema structure:")
    print(json.dumps(schema, indent=2))

    # Test with example prompts
    if schema_name == "code_review":
        prompt = "Review this Python code for bugs and improvements:\n\ndef calculate_average(numbers):\n    return sum(numbers) / len(numbers)"
    elif schema_name == "document_summary":
        prompt = "Summarize this document about climate change and its effects on global ecosystems."
    else:  # image_analysis
        prompt = "Analyze this image of a city skyline at sunset."

    print(f"\nTesting with prompt: {prompt}")

    try:
        # Get response from OpenRouter
        response = await client.chat.completions.create(
            model=client.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )

        # Process streaming response
        print("\nResponse:")
        print("-" * 30)
        full_response = ""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content

        print("\n\nValidating response...")

        # Validate response
        is_valid, errors = schema_manager.validate_response(full_response)
        if is_valid:
            print("Response is valid according to schema")
        else:
            print("Response validation failed:")
            print(json.dumps(errors, indent=2))

    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    # Initialize key manager
    key_manager = OpenRouterKeyManager()
    if not key_manager.has_keys():
        print("No API keys found. Please set up your API keys first.")
        return

    # Create OpenRouter client
    client = create_client(api_key=key_manager.get_random_key())

    # Initialize schema manager with example schemas
    schema_manager = SchemaManager()
    for name, schema in SCHEMAS.items():
        schema_manager.add_schema(name, schema)

    while True:
        print("\nOpenRouter Schema Management")
        print("1. List available schemas")
        print("2. Test code review schema")
        print("3. Test document summary schema")
        print("4. Test image analysis schema")
        print("5. Exit")

        choice = input("\nSelect option (1-5): ").strip()

        if choice == "1":
            print("\nAvailable schemas:")
            for name in schema_manager.list_schemas():
                print(f"- {name}")

        elif choice == "2":
            await test_schema(schema_manager, client, "code_review")

        elif choice == "3":
            await test_schema(schema_manager, client, "document_summary")

        elif choice == "4":
            await test_schema(schema_manager, client, "image_analysis")

        elif choice == "5":
            break

        else:
            print("Invalid option")

if __name__ == "__main__":
    asyncio.run(main())
