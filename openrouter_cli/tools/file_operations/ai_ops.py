"""
AI-powered file operations.
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from ..openrouter_client import create_client
from .base import FileOperationsBase

logger = logging.getLogger(__name__)

class AIPoweredFileOperations(FileOperationsBase):
    """AI-powered file operations with OpenRouter integration."""

    def __init__(
        self,
        base_dir: str = ".",
        api_key: Optional[str] = None,
        allowed_extensions: Optional[List[str]] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        cache_dir: str = ".ai_cache",
        cache_ttl: int = 3600  # 1 hour
    ):
        super().__init__(base_dir, allowed_extensions, max_file_size)
        self.client = create_client(api_key=api_key)
        self.cache_dir = Path(cache_dir)
        self.cache_ttl = cache_ttl

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, file_path: str) -> Path:
        """Get cache file path for a given file."""
        file_hash = str(Path(file_path).absolute())
        return self.cache_dir / f"{hash(file_hash)}.json"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache is still valid."""
        if not cache_path.exists():
            return False
        age = time.time() - cache_path.stat().st_mtime
        return age < self.cache_ttl

    async def analyze_file(
        self,
        file_path: str,
        prompt: str,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze a file using AI."""
        try:
            if not self.validate_file(file_path):
                raise ValueError(f"Invalid file: {file_path}")

            # Check cache
            cache_path = self._get_cache_path(file_path)
            if self._is_cache_valid(cache_path):
                with open(cache_path, 'r') as f:
                    result = json.load(f)
                result["cache_hit"] = True
                return result

            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()

            # Prepare messages
            messages = [
                {"role": "system", "content": "You are a file analysis assistant."},
                {"role": "user", "content": f"{prompt}\n\nFile content:\n{content}"}
            ]

            # Get AI response
            start_time = time.time()
            response = await self.client.chat.completions.create(
                model=model or self.client.model,
                messages=messages,
                stream=True
            )

            # Process streaming response
            full_response = ""
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content

            processing_time = time.time() - start_time

            # Prepare result
            result = {
                "analysis": full_response,
                "model": model or self.client.model,
                "processing_time": processing_time,
                "cache_hit": False
            }

            # Cache result
            with open(cache_path, 'w') as f:
                json.dump(result, f)

            return result

        except Exception as e:
            logger.error(f"Error analyzing file: {e}")
            raise

    async def batch_analyze_files(
        self,
        file_paths: List[str],
        prompt: str,
        model: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze multiple files using AI."""
        results = {}
        for file_path in file_paths:
            try:
                results[file_path] = await self.analyze_file(
                    file_path,
                    prompt,
                    model
                )
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {e}")
                results[file_path] = {
                    "error": str(e),
                    "model": model or self.client.model,
                    "processing_time": 0,
                    "cache_hit": False
                }
        return results

    async def clear_cache(self) -> bool:
        """Clear the cache directory."""
        try:
            if self.cache_dir.exists():
                for file in self.cache_dir.glob("*.json"):
                    file.unlink()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
