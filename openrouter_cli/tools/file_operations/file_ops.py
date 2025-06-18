"""
File operations implementation.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional
from .base import FileOperationsBase

logger = logging.getLogger(__name__)

class FileOperations(FileOperationsBase):
    """File operations implementation."""

    def list_files(self, pattern: str = "*") -> List[Dict]:
        """List files in base directory matching pattern."""
        try:
            files = []
            for path in self.base_dir.glob(pattern):
                if path.is_file() and self.validate_file(str(path)):
                    files.append({
                        "path": str(path),
                        "size": self.get_file_size(str(path)),
                        "extension": path.suffix.lower()
                    })
            return files
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []

    def copy_file(self, source: str, destination: str) -> bool:
        """Copy a file from source to destination."""
        try:
            if not self.validate_file(source):
                return False

            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(source, destination)
            return True
        except Exception as e:
            logger.error(f"Error copying file: {e}")
            return False

    def move_file(self, source: str, destination: str) -> bool:
        """Move a file from source to destination."""
        try:
            if not self.validate_file(source):
                return False

            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(source, destination)
            return True
        except Exception as e:
            logger.error(f"Error moving file: {e}")
            return False

    def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        try:
            if not self.validate_file_path(file_path):
                return False

            os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False

    def create_directory(self, dir_path: str) -> bool:
        """Create a directory."""
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory: {e}")
            return False

    def delete_directory(self, dir_path: str) -> bool:
        """Delete a directory and its contents."""
        try:
            shutil.rmtree(dir_path)
            return True
        except Exception as e:
            logger.error(f"Error deleting directory: {e}")
            return False
