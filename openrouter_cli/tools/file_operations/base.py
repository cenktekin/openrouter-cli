"""
Base class for file operations.
"""

import os
import mimetypes
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class FileOperationsBase:
    """Base class for file operations."""

    def __init__(
        self,
        base_dir: str = ".",
        allowed_extensions: Optional[List[str]] = None,
        max_file_size: int = 10 * 1024 * 1024  # 10MB
    ):
        self.base_dir = Path(base_dir)
        self.allowed_extensions = allowed_extensions or [
            ".txt", ".md", ".pdf", ".jpg", ".jpeg", ".png",
            ".py", ".js", ".java", ".cpp", ".h"
        ]
        self.max_file_size = max_file_size

    def validate_file_path(self, file_path: str) -> bool:
        """Validate file path."""
        try:
            path = Path(file_path)
            return path.exists() and path.is_file()
        except Exception as e:
            logger.error(f"Error validating file path: {e}")
            return False

    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"Error getting file size: {e}")
            return 0

    def is_allowed_extension(self, file_path: str) -> bool:
        """Check if file extension is allowed."""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            return ext in self.allowed_extensions
        except Exception as e:
            logger.error(f"Error checking file extension: {e}")
            return False

    def validate_file(self, file_path: str) -> bool:
        """Validate file path, size, and extension."""
        if not self.validate_file_path(file_path):
            logger.error(f"Invalid file path: {file_path}")
            return False

        if not self.is_allowed_extension(file_path):
            logger.error(f"File extension not allowed: {file_path}")
            return False

        size = self.get_file_size(file_path)
        if size > self.max_file_size:
            logger.error(f"File too large: {file_path} ({size} bytes)")
            return False

        return True

class FileOperationsTool(FileOperationsBase):
    """Tool for file operations with additional functionality."""

    def __init__(
        self,
        base_dir: str = ".",
        allowed_extensions: Optional[List[str]] = None,
        max_file_size: int = 100 * 1024 * 1024  # 100MB default
    ):
        super().__init__(base_dir, allowed_extensions, max_file_size)
        self.base_dir = Path(base_dir).resolve()
        self.allowed_extensions = set(ext.lower() for ext in (allowed_extensions or []))
        self.max_file_size = max_file_size

        # Initialize mimetypes
        mimetypes.init()

    def _is_safe_path(self, path: Path) -> bool:
        """Check if a path is within the base directory."""
        try:
            return self.base_dir in path.resolve().parents or path.resolve() == self.base_dir
        except Exception:
            return False

    def _is_allowed_file(self, path: Path) -> bool:
        """Check if a file type is allowed."""
        if not self.allowed_extensions:
            return True
        return path.suffix.lower() in self.allowed_extensions

    def _calculate_hash(self, path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        hash_obj = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def _get_file_list(self, dir_path: Path, exclude_patterns: Optional[List[str]] = None) -> Dict[Path, Dict]:
        """Get a list of files in a directory with their metadata."""
        files = {}
        exclude_patterns = exclude_patterns or []

        for path in dir_path.rglob('*'):
            if path.is_file():
                # Check if file should be excluded
                if any(path.match(pattern) for pattern in exclude_patterns):
                    continue

                # Get file metadata
                stat = path.stat()
                files[path] = {
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "type": mimetypes.guess_type(str(path))[0] or 'application/octet-stream',
                    "hash": self._calculate_hash(path)
                }
