import requests
import base64
from typing import Dict
from rich.console import Console
from pathlib import Path
import os

console = Console()

class ImageGenerationTool:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("STABLE_DIFFUSION_API_KEY")
        self.base_url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.output_dir = Path("generated_images")
        self.output_dir.mkdir(exist_ok=True)

    def generate(self, prompt: str, size: str = "1024x1024", num_images: int = 1) -> Dict:
        """Generate images using Stable Diffusion API."""
        if not self.api_key:
            return {
                "error": "API key not found. Please set STABLE_DIFFUSION_API_KEY environment variable."
            }

        try:
            width, height = map(int, size.split("x"))

            body = {
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": height,
                "width": width,
                "samples": num_images,
                "steps": 30,
            }

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=body,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            image_paths = []

            for i, image in enumerate(data["artifacts"]):
                # Save image to file
                image_path = self.output_dir / f"generated_{i+1}.png"
                with open(image_path, "wb") as f:
                    f.write(base64.b64decode(image["base64"]))
                image_paths.append(str(image_path))

            return {
                "image_paths": image_paths,
                "prompt": prompt,
                "size": size,
                "num_images": num_images
            }

        except requests.RequestException as e:
            console.print(f"[red]Error during image generation: {str(e)}[/red]")
            return {
                "error": str(e)
            }
        except Exception as e:
            console.print(f"[red]Unexpected error: {str(e)}[/red]")
            return {
                "error": str(e)
            }
