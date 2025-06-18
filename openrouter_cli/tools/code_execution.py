import subprocess
import tempfile
import os
from typing import Dict
from rich.console import Console
import docker
import json

console = Console()

class CodeExecutionTool:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.timeout = 30  # seconds
        self.max_output_size = 1024 * 1024  # 1MB

    def execute(self, code: str, language: str = "python") -> Dict:
        """Execute code in a sandboxed Docker container."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix=self._get_file_extension(language), delete=False) as f:
                f.write(code)
                temp_file = f.name

            # Get Docker image based on language
            image = self._get_docker_image(language)

            # Run code in container
            container = self.docker_client.containers.run(
                image,
                command=self._get_execution_command(language, temp_file),
                volumes={temp_file: {'bind': f'/app/{os.path.basename(temp_file)}', 'mode': 'ro'}},
                detach=True,
                mem_limit='512m',
                cpu_period=100000,
                cpu_quota=50000,  # 50% CPU limit
                network_disabled=True
            )

            try:
                # Wait for container to finish
                container.wait(timeout=self.timeout)

                # Get output
                output = container.logs(stdout=True, stderr=True).decode('utf-8')

                # Get exit code
                exit_code = container.attrs['State']['ExitCode']

                return {
                    "output": output[:self.max_output_size],
                    "exit_code": exit_code,
                    "language": language,
                    "truncated": len(output) > self.max_output_size
                }

            finally:
                # Clean up
                container.remove(force=True)
                os.unlink(temp_file)

        except docker.errors.APIError as e:
            console.print(f"[red]Docker API error: {str(e)}[/red]")
            return {
                "error": f"Docker API error: {str(e)}"
            }
        except Exception as e:
            console.print(f"[red]Unexpected error: {str(e)}[/red]")
            return {
                "error": str(e)
            }

    def _get_file_extension(self, language: str) -> str:
        """Get file extension for the given language."""
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "cpp": ".cpp",
            "c": ".c",
            "rust": ".rs",
            "go": ".go"
        }
        return extensions.get(language.lower(), ".txt")

    def _get_docker_image(self, language: str) -> str:
        """Get Docker image for the given language."""
        images = {
            "python": "python:3.9-slim",
            "javascript": "node:16-slim",
            "typescript": "node:16-slim",
            "java": "openjdk:11-slim",
            "cpp": "gcc:latest",
            "c": "gcc:latest",
            "rust": "rust:1.67-slim",
            "go": "golang:1.19-slim"
        }
        return images.get(language.lower(), "python:3.9-slim")

    def _get_execution_command(self, language: str, file_path: str) -> str:
        """Get command to execute code for the given language."""
        filename = os.path.basename(file_path)
        commands = {
            "python": f"python /app/{filename}",
            "javascript": f"node /app/{filename}",
            "typescript": f"ts-node /app/{filename}",
            "java": f"javac /app/{filename} && java -cp /app {os.path.splitext(filename)[0]}",
            "cpp": f"g++ /app/{filename} -o /app/program && /app/program",
            "c": f"gcc /app/{filename} -o /app/program && /app/program",
            "rust": f"rustc /app/{filename} && /app/{os.path.splitext(filename)[0]}",
            "go": f"go run /app/{filename}"
        }
        return commands.get(language.lower(), f"python /app/{filename}")
