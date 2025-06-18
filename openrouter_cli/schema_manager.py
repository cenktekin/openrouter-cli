"""
Schema manager for OpenRouter CLI.
"""

import os
import yaml
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

class SchemaManager:
    def __init__(self, schemas_dir: str = "schemas"):
        self.schemas_dir = Path(__file__).parent / schemas_dir
        # print(self.schemas_dir)
        self.schemas: Dict[str, Dict] = {}
        self.current_schema: Optional[str] = None
        self.load_schemas()

    def load_schemas(self) -> None:
        """Load all schema files from the schemas directory."""
        if not self.schemas_dir.exists():
            console.print(f"[red]Schemas directory not found: {self.schemas_dir}[/red]")
            return

        for schema_file in self.schemas_dir.glob("*.yaml"):
            try:
                with open(schema_file, 'r') as f:
                    schema_data = yaml.safe_load(f)
                    if schema_data and 'name' in schema_data and 'schema' in schema_data:
                        self.schemas[schema_data['name']] = schema_data
            except Exception as e:
                console.print(f"[red]Error loading schema {schema_file}: {str(e)}[/red]")

    def list_schemas(self) -> None:
        """Display available schemas in a table."""
        if not self.schemas:
            console.print("[yellow]No schemas available[/yellow]")
            return

        table = Table(title="Available Schemas")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Status", style="yellow")

        for name, schema in self.schemas.items():
            status = "✓ Current" if name == self.current_schema else ""
            table.add_row(
                name,
                schema.get('description', ''),
                status
            )

        console.print(table)

    def get_schema(self, name: str) -> Optional[Dict]:
        """Get a schema by name."""
        return self.schemas.get(name)

    def use_schema(self, name: str) -> bool:
        """Set the current schema."""
        if name in self.schemas:
            self.current_schema = name
            return True
        return False

    def get_current_schema(self) -> Optional[Dict]:
        """Get the current schema configuration."""
        if self.current_schema:
            return self.schemas.get(self.current_schema)
        return None

    def get_response_format(self) -> Optional[Dict]:
        """Get the response format for the current schema."""
        schema = self.get_current_schema()
        if schema and 'schema' in schema:
            return {
                "type": "json_schema",
                "json_schema": schema['schema']
            }
        return None

    def validate_response(self, response: str) -> tuple[bool, List[str]]:
        """Validate a response against the current schema and return validation errors."""
        try:
            # For chat schema, wrap plain text in a response object
            if self.current_schema == "chat":
                data = {"response": response}
            else:
                # Try to parse as JSON for other schemas
                try:
                    data = json.loads(response)
                except json.JSONDecodeError:
                    return False, ["Invalid JSON response"]

            schema = self.get_current_schema()
            errors = []

            if not schema or 'schema' not in schema:
                return True, []

            # Check required fields
            required = schema['schema'].get('required', [])
            for field in required:
                if field not in data:
                    errors.append(f"Missing required field: {field}")

            # Check field types
            properties = schema['schema'].get('properties', {})
            for field, value in data.items():
                if field in properties:
                    field_schema = properties[field]
                    if not self._validate_field_type(value, field_schema):
                        errors.append(f"Invalid type for field '{field}': expected {field_schema.get('type')}")

            return len(errors) == 0, errors

        except Exception as e:
            return False, [str(e)]

    def _validate_field_type(self, value: Any, field_schema: Dict) -> bool:
        """Validate a field's value against its schema type."""
        field_type = field_schema.get('type')

        if field_type == 'string':
            return isinstance(value, str)
        elif field_type == 'number':
            return isinstance(value, (int, float))
        elif field_type == 'boolean':
            return isinstance(value, bool)
        elif field_type == 'array':
            if not isinstance(value, list):
                return False
            if 'items' in field_schema:
                item_schema = field_schema['items']
                return all(self._validate_field_type(item, item_schema) for item in value)
            return True
        elif field_type == 'object':
            if not isinstance(value, dict):
                return False
            if 'properties' in field_schema:
                properties = field_schema['properties']
                return all(self._validate_field_type(value.get(k), v) for k, v in properties.items())
            return True

        return True

    def format_response(self, response: str, format_type: str = "pretty") -> str:
        """Format a structured response based on the format type."""
        try:
            # For chat schema, wrap plain text in a response object
            if self.current_schema == "chat":
                data = {"response": response}
            else:
                # Try to parse as JSON for other schemas
                try:
                    data = json.loads(response)
                except json.JSONDecodeError:
                    return response

            schema = self.get_current_schema()

            if not schema or 'schema' not in schema:
                return response

            if format_type == "json":
                return json.dumps(data, indent=2)

            elif format_type == "compact":
                # Return the main response field if available
                main_field = next(iter(schema['schema'].get('properties', {})), None)
                return data.get(main_field, response)

            elif format_type == "pretty":
                # Create a rich formatted output
                output = []

                # Add main content
                for field, value in data.items():
                    if isinstance(value, (str, int, float, bool)):
                        output.append(f"[bold cyan]{field.title()}:[/bold cyan] {value}")
                    elif isinstance(value, list):
                        output.append(f"\n[bold cyan]{field.title()}:[/bold cyan]")
                        for item in value:
                            if isinstance(item, dict):
                                for k, v in item.items():
                                    output.append(f"  • {k}: {v}")
                            else:
                                output.append(f"  • {item}")
                    elif isinstance(value, dict):
                        output.append(f"\n[bold cyan]{field.title()}:[/bold cyan]")
                        for k, v in value.items():
                            output.append(f"  • {k}: {v}")

                return "\n".join(output)

            return response

        except Exception as e:
            return response
