import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Set
from rich.console import Console
import mimetypes
import hashlib
import fnmatch
import zipfile
import difflib
import re
import gzip
import bz2
import lzma
import struct
import binascii
from datetime import datetime
import time
import json
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import tarfile
import tempfile

console = Console()

class FileOperationsTool:
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.allowed_extensions = {
            '.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.yaml', '.yml',
            '.csv', '.xml', '.log', '.ini', '.conf', '.env', '.sh', '.bat'
        }
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.compression_formats = {
            'zip': zipfile.ZipFile,
            'gz': gzip.open,
            'bz2': bz2.open,
            'xz': lzma.open
        }
        self.binary_patterns = {
            'hex': re.compile(r'^[0-9A-Fa-f\s]+$'),
            'binary': re.compile(r'^[01\s]+$'),
            'ascii': re.compile(r'^[\x20-\x7E\s]+$')
        }

    def read_file(self, file_path: str) -> Dict:
        """Read a file's contents."""
        try:
            full_path = self.base_dir / file_path

            # Security checks
            if not self._is_safe_path(full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not full_path.exists():
                return {"error": f"File not found: {file_path}"}

            if not self._is_allowed_file(full_path):
                return {"error": f"File type not allowed: {file_path}"}

            if full_path.stat().st_size > self.max_file_size:
                return {"error": f"File too large: {file_path}"}

            # Read file
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                "content": content,
                "path": str(full_path),
                "size": full_path.stat().st_size,
                "type": mimetypes.guess_type(str(full_path))[0] or "text/plain",
                "hash": self._calculate_hash(full_path)
            }

        except Exception as e:
            return {"error": str(e)}

    def write_file(self, file_path: str, content: str, overwrite: bool = False) -> Dict:
        """Write content to a file."""
        try:
            full_path = self.base_dir / file_path

            # Security checks
            if not self._is_safe_path(full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not self._is_allowed_file(full_path):
                return {"error": f"File type not allowed: {file_path}"}

            if full_path.exists() and not overwrite:
                return {"error": f"File already exists: {file_path}"}

            # Create directory if it doesn't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                "path": str(full_path),
                "size": full_path.stat().st_size,
                "type": mimetypes.guess_type(str(full_path))[0] or "text/plain",
                "hash": self._calculate_hash(full_path)
            }

        except Exception as e:
            return {"error": str(e)}

    def list_directory(self, dir_path: str = ".") -> Dict:
        """List contents of a directory."""
        try:
            full_path = self.base_dir / dir_path

            # Security checks
            if not self._is_safe_path(full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not full_path.exists():
                return {"error": f"Directory not found: {dir_path}"}

            if not full_path.is_dir():
                return {"error": f"Not a directory: {dir_path}"}

            # List contents
            contents = []
            for item in full_path.iterdir():
                if item.is_file() and self._is_allowed_file(item):
                    contents.append({
                        "name": item.name,
                        "type": "file",
                        "size": item.stat().st_size,
                        "modified": item.stat().st_mtime
                    })
                elif item.is_dir():
                    contents.append({
                        "name": item.name,
                        "type": "directory",
                        "size": None,
                        "modified": item.stat().st_mtime
                    })

            return {
                "path": str(full_path),
                "contents": contents,
                "total_files": len([c for c in contents if c["type"] == "file"]),
                "total_dirs": len([c for c in contents if c["type"] == "directory"])
            }

        except Exception as e:
            return {"error": str(e)}

    def delete_file(self, file_path: str) -> Dict:
        """Delete a file."""
        try:
            full_path = self.base_dir / file_path

            # Security checks
            if not self._is_safe_path(full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not full_path.exists():
                return {"error": f"File not found: {file_path}"}

            if not self._is_allowed_file(full_path):
                return {"error": f"File type not allowed: {file_path}"}

            # Delete file
            full_path.unlink()

            return {
                "message": f"File deleted: {file_path}",
                "path": str(full_path)
            }

        except Exception as e:
            return {"error": str(e)}

    def copy_file(self, source_path: str, dest_path: str, overwrite: bool = False) -> Dict:
        """Copy a file from source to destination."""
        try:
            source_full_path = self.base_dir / source_path
            dest_full_path = self.base_dir / dest_path

            # Security checks
            if not self._is_safe_path(source_full_path) or not self._is_safe_path(dest_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not source_full_path.exists():
                return {"error": f"Source file not found: {source_path}"}

            if not self._is_allowed_file(source_full_path):
                return {"error": f"Source file type not allowed: {source_path}"}

            if dest_full_path.exists() and not overwrite:
                return {"error": f"Destination file already exists: {dest_path}"}

            # Create destination directory if it doesn't exist
            dest_full_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(source_full_path, dest_full_path)

            return {
                "message": f"File copied: {source_path} -> {dest_path}",
                "source": str(source_full_path),
                "destination": str(dest_full_path),
                "size": dest_full_path.stat().st_size,
                "type": mimetypes.guess_type(str(dest_full_path))[0] or "text/plain",
                "hash": self._calculate_hash(dest_full_path)
            }

        except Exception as e:
            return {"error": str(e)}

    def move_file(self, source_path: str, dest_path: str, overwrite: bool = False) -> Dict:
        """Move a file from source to destination."""
        try:
            source_full_path = self.base_dir / source_path
            dest_full_path = self.base_dir / dest_path

            # Security checks
            if not self._is_safe_path(source_full_path) or not self._is_safe_path(dest_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not source_full_path.exists():
                return {"error": f"Source file not found: {source_path}"}

            if not self._is_allowed_file(source_full_path):
                return {"error": f"Source file type not allowed: {source_path}"}

            if dest_full_path.exists() and not overwrite:
                return {"error": f"Destination file already exists: {dest_path}"}

            # Create destination directory if it doesn't exist
            dest_full_path.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(source_full_path, dest_full_path)

            return {
                "message": f"File moved: {source_path} -> {dest_path}",
                "source": str(source_full_path),
                "destination": str(dest_full_path),
                "size": dest_full_path.stat().st_size,
                "type": mimetypes.guess_type(str(dest_full_path))[0] or "text/plain",
                "hash": self._calculate_hash(dest_full_path)
            }

        except Exception as e:
            return {"error": str(e)}

    def search_files(self, pattern: str, dir_path: str = ".", recursive: bool = True) -> Dict:
        """Search for files matching a pattern."""
        try:
            full_path = self.base_dir / dir_path

            # Security checks
            if not self._is_safe_path(full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not full_path.exists():
                return {"error": f"Directory not found: {dir_path}"}

            if not full_path.is_dir():
                return {"error": f"Not a directory: {dir_path}"}

            # Search files
            matches = []
            for root, _, files in os.walk(full_path) if recursive else [(full_path, [], [f.name for f in full_path.iterdir() if f.is_file()])]:
                for file in files:
                    if fnmatch.fnmatch(file, pattern):
                        file_path = Path(root) / file
                        if self._is_allowed_file(file_path):
                            matches.append({
                                "name": file,
                                "path": str(file_path.relative_to(self.base_dir)),
                                "size": file_path.stat().st_size,
                                "modified": file_path.stat().st_mtime,
                                "type": mimetypes.guess_type(str(file_path))[0] or "text/plain"
                            })

            return {
                "pattern": pattern,
                "directory": str(full_path),
                "recursive": recursive,
                "matches": matches,
                "total_matches": len(matches)
            }

        except Exception as e:
            return {"error": str(e)}

    def _is_safe_path(self, path: Path) -> bool:
        """Check if path is within base directory."""
        try:
            return path.resolve().is_relative_to(self.base_dir.resolve())
        except ValueError:
            return False

    def _is_allowed_file(self, path: Path) -> bool:
        """Check if file type is allowed."""
        return path.suffix.lower() in self.allowed_extensions

    def _calculate_hash(self, path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def compress_file(self, file_path: str, format: str = 'zip', delete_original: bool = False) -> Dict:
        """Compress a file using the specified format."""
        try:
            if format not in self.compression_formats:
                return {"error": f"Unsupported compression format: {format}"}

            full_path = self.base_dir / file_path

            # Security checks
            if not self._is_safe_path(full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not full_path.exists():
                return {"error": f"File not found: {file_path}"}

            if not self._is_allowed_file(full_path):
                return {"error": f"File type not allowed: {file_path}"}

            # Create compressed file
            compressed_path = full_path.with_suffix(full_path.suffix + f'.{format}')

            if format == 'zip':
                with zipfile.ZipFile(compressed_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(full_path, full_path.name)
            else:
                with self.compression_formats[format](compressed_path, 'wb') as f_out:
                    with open(full_path, 'rb') as f_in:
                        f_out.write(f_in.read())

            # Delete original if requested
            if delete_original:
                full_path.unlink()

            return {
                "message": f"File compressed: {file_path} -> {compressed_path.name}",
                "original": str(full_path),
                "compressed": str(compressed_path),
                "original_size": full_path.stat().st_size,
                "compressed_size": compressed_path.stat().st_size,
                "compression_ratio": full_path.stat().st_size / compressed_path.stat().st_size
            }

        except Exception as e:
            return {"error": str(e)}

    def search_content(self, pattern: str, dir_path: str = ".", recursive: bool = True,
                      case_sensitive: bool = False, max_results: int = 100) -> Dict:
        """Search for content within files."""
        try:
            full_path = self.base_dir / dir_path

            # Security checks
            if not self._is_safe_path(full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not full_path.exists():
                return {"error": f"Directory not found: {dir_path}"}

            if not full_path.is_dir():
                return {"error": f"Not a directory: {dir_path}"}

            # Compile pattern
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)

            # Search files
            matches = []
            for root, _, files in os.walk(full_path) if recursive else [(full_path, [], [f.name for f in full_path.iterdir() if f.is_file()])]:
                for file in files:
                    if len(matches) >= max_results:
                        break

                    file_path = Path(root) / file
                    if self._is_allowed_file(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                for line_num, line in enumerate(f, 1):
                                    if regex.search(line):
                                        matches.append({
                                            "file": str(file_path.relative_to(self.base_dir)),
                                            "line": line_num,
                                            "content": line.strip(),
                                            "context": self._get_context(file_path, line_num)
                                        })
                                        if len(matches) >= max_results:
                                            break
                        except UnicodeDecodeError:
                            continue

            return {
                "pattern": pattern,
                "directory": str(full_path),
                "recursive": recursive,
                "case_sensitive": case_sensitive,
                "matches": matches,
                "total_matches": len(matches),
                "max_results": max_results
            }

        except Exception as e:
            return {"error": str(e)}

    def compare_files(self, file1_path: str, file2_path: str, context_lines: int = 3) -> Dict:
        """Compare two files and show differences."""
        try:
            file1_full_path = self.base_dir / file1_path
            file2_full_path = self.base_dir / file2_path

            # Security checks
            if not self._is_safe_path(file1_full_path) or not self._is_safe_path(file2_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not file1_full_path.exists() or not file2_full_path.exists():
                return {"error": "One or both files not found"}

            if not self._is_allowed_file(file1_full_path) or not self._is_allowed_file(file2_full_path):
                return {"error": "One or both file types not allowed"}

            # Read files
            with open(file1_full_path, 'r', encoding='utf-8') as f1, \
                 open(file2_full_path, 'r', encoding='utf-8') as f2:
                file1_lines = f1.readlines()
                file2_lines = f2.readlines()

            # Compare files
            differ = difflib.Differ()
            diff = list(differ.compare(file1_lines, file2_lines))

            # Process differences
            differences = []
            current_diff = []
            line_num = 0

            for line in diff:
                line_num += 1
                if line.startswith(('+', '-', '?')):
                    current_diff.append((line_num, line))
                elif current_diff:
                    differences.append(current_diff)
                    current_diff = []

            if current_diff:
                differences.append(current_diff)

            return {
                "file1": str(file1_full_path),
                "file2": str(file2_full_path),
                "differences": differences,
                "total_differences": len(differences),
                "file1_size": file1_full_path.stat().st_size,
                "file2_size": file2_full_path.stat().st_size,
                "file1_hash": self._calculate_hash(file1_full_path),
                "file2_hash": self._calculate_hash(file2_full_path)
            }

        except Exception as e:
            return {"error": str(e)}

    def _get_context(self, file_path: Path, line_num: int, context_lines: int = 3) -> List[str]:
        """Get context lines around a specific line number."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                start = max(0, line_num - context_lines - 1)
                end = min(len(lines), line_num + context_lines)
                return [line.strip() for line in lines[start:end]]
        except:
            return []

    def compare_binary_files(self, file1_path: str, file2_path: str, chunk_size: int = 1024) -> Dict:
        """Compare two files in binary mode."""
        try:
            file1_full_path = self.base_dir / file1_path
            file2_full_path = self.base_dir / file2_path

            # Security checks
            if not self._is_safe_path(file1_full_path) or not self._is_safe_path(file2_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not file1_full_path.exists() or not file2_full_path.exists():
                return {"error": "One or both files not found"}

            # Compare files
            differences = []
            offset = 0

            with open(file1_full_path, 'rb') as f1, open(file2_full_path, 'rb') as f2:
                while True:
                    chunk1 = f1.read(chunk_size)
                    chunk2 = f2.read(chunk_size)

                    if not chunk1 and not chunk2:
                        break

                    if chunk1 != chunk2:
                        # Find the first difference in this chunk
                        for i, (b1, b2) in enumerate(zip(chunk1, chunk2)):
                            if b1 != b2:
                                differences.append({
                                    "offset": offset + i,
                                    "file1_byte": hex(b1),
                                    "file2_byte": hex(b2),
                                    "file1_ascii": chr(b1) if 32 <= b1 <= 126 else '.',
                                    "file2_ascii": chr(b2) if 32 <= b2 <= 126 else '.'
                                })

                    offset += len(chunk1)

            return {
                "file1": str(file1_full_path),
                "file2": str(file2_full_path),
                "differences": differences,
                "total_differences": len(differences),
                "file1_size": file1_full_path.stat().st_size,
                "file2_size": file2_full_path.stat().st_size,
                "file1_hash": self._calculate_hash(file1_full_path),
                "file2_hash": self._calculate_hash(file2_full_path)
            }

        except Exception as e:
            return {"error": str(e)}

    def merge_files(self, file1_path: str, file2_path: str, output_path: str,
                   strategy: str = 'interleave', separator: str = '\n') -> Dict:
        """Merge two files using the specified strategy."""
        try:
            file1_full_path = self.base_dir / file1_path
            file2_full_path = self.base_dir / file2_path
            output_full_path = self.base_dir / output_path

            # Security checks
            if not all(self._is_safe_path(p) for p in [file1_full_path, file2_full_path, output_full_path]):
                return {"error": "Access denied: Path outside base directory"}

            if not file1_full_path.exists() or not file2_full_path.exists():
                return {"error": "One or both input files not found"}

            if not self._is_allowed_file(file1_full_path) or not self._is_allowed_file(file2_full_path):
                return {"error": "One or both file types not allowed"}

            # Read files
            with open(file1_full_path, 'r', encoding='utf-8') as f1, \
                 open(file2_full_path, 'r', encoding='utf-8') as f2:
                file1_lines = f1.readlines()
                file2_lines = f2.readlines()

            # Merge files based on strategy
            if strategy == 'interleave':
                merged_lines = []
                for l1, l2 in zip(file1_lines, file2_lines):
                    merged_lines.extend([l1.rstrip(), l2.rstrip(), separator])
                if len(file1_lines) > len(file2_lines):
                    merged_lines.extend(l.rstrip() + separator for l in file1_lines[len(file2_lines):])
                elif len(file2_lines) > len(file1_lines):
                    merged_lines.extend(l.rstrip() + separator for l in file2_lines[len(file1_lines):])
            elif strategy == 'append':
                merged_lines = file1_lines + [separator] + file2_lines
            elif strategy == 'prepend':
                merged_lines = file2_lines + [separator] + file1_lines
            else:
                return {"error": f"Unsupported merge strategy: {strategy}"}

            # Write merged file
            output_full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_full_path, 'w', encoding='utf-8') as f:
                f.writelines(merged_lines)

            return {
                "message": f"Files merged using {strategy} strategy",
                "file1": str(file1_full_path),
                "file2": str(file2_full_path),
                "output": str(output_full_path),
                "file1_lines": len(file1_lines),
                "file2_lines": len(file2_lines),
                "merged_lines": len(merged_lines),
                "strategy": strategy
            }

        except Exception as e:
            return {"error": str(e)}

    def search_content_advanced(self, pattern: str, dir_path: str = ".", recursive: bool = True,
                              case_sensitive: bool = False, whole_word: bool = False,
                              file_types: Optional[List[str]] = None, max_results: int = 100,
                              context_lines: int = 3, binary_search: bool = False) -> Dict:
        """Advanced content search with additional options."""
        try:
            full_path = self.base_dir / dir_path

            # Security checks
            if not self._is_safe_path(full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not full_path.exists():
                return {"error": f"Directory not found: {dir_path}"}

            if not full_path.is_dir():
                return {"error": f"Not a directory: {dir_path}"}

            # Prepare pattern
            if whole_word:
                pattern = r'\b' + re.escape(pattern) + r'\b'
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)

            # Search files
            matches = []
            for root, _, files in os.walk(full_path) if recursive else [(full_path, [], [f.name for f in full_path.iterdir() if f.is_file()])]:
                for file in files:
                    if len(matches) >= max_results:
                        break

                    file_path = Path(root) / file
                    if self._is_allowed_file(file_path) and (not file_types or file_path.suffix.lower() in file_types):
                        try:
                            mode = 'rb' if binary_search else 'r'
                            encoding = None if binary_search else 'utf-8'
                            with open(file_path, mode, encoding=encoding) as f:
                                if binary_search:
                                    content = f.read()
                                    for match in regex.finditer(content):
                                        start = max(0, match.start() - 20)
                                        end = min(len(content), match.end() + 20)
                                        context = binascii.hexlify(content[start:end]).decode('ascii')
                                        matches.append({
                                            "file": str(file_path.relative_to(self.base_dir)),
                                            "offset": match.start(),
                                            "content": binascii.hexlify(match.group()).decode('ascii'),
                                            "context": context
                                        })
                                else:
                                    for line_num, line in enumerate(f, 1):
                                        if regex.search(line):
                                            matches.append({
                                                "file": str(file_path.relative_to(self.base_dir)),
                                                "line": line_num,
                                                "content": line.strip(),
                                                "context": self._get_context(file_path, line_num, context_lines)
                                            })
                                        if len(matches) >= max_results:
                                            break
                        except UnicodeDecodeError:
                            continue

            return {
                "pattern": pattern,
                "directory": str(full_path),
                "recursive": recursive,
                "case_sensitive": case_sensitive,
                "whole_word": whole_word,
                "file_types": file_types,
                "binary_search": binary_search,
                "matches": matches,
                "total_matches": len(matches),
                "max_results": max_results
            }

        except Exception as e:
            return {"error": str(e)}

    def sync_directories(self, source_dir: str, target_dir: str,
                        sync_type: str = 'mirror',
                        exclude_patterns: Optional[List[str]] = None) -> Dict:
        """Synchronize two directories with different strategies."""
        try:
            source_full_path = self.base_dir / source_dir
            target_full_path = self.base_dir / target_dir

            # Security checks
            if not self._is_safe_path(source_full_path) or not self._is_safe_path(target_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not source_full_path.exists() or not source_full_path.is_dir():
                return {"error": f"Source directory not found: {source_dir}"}

            # Create target directory if it doesn't exist
            target_full_path.mkdir(parents=True, exist_ok=True)

            # Initialize sync statistics
            stats = {
                "copied": 0,
                "updated": 0,
                "deleted": 0,
                "skipped": 0,
                "errors": 0
            }

            # Get file lists
            source_files = self._get_file_list(source_full_path, exclude_patterns)
            target_files = self._get_file_list(target_full_path, exclude_patterns)

            # Perform sync based on strategy
            if sync_type == 'mirror':
                # Mirror source to target (delete extra files in target)
                for rel_path, target_info in target_files.items():
                    if rel_path not in source_files:
                        try:
                            (target_full_path / rel_path).unlink()
                            stats["deleted"] += 1
                        except Exception:
                            stats["errors"] += 1

            # Copy/update files
            for rel_path, source_info in source_files.items():
                source_path = source_full_path / rel_path
                target_path = target_full_path / rel_path

                try:
                    if not target_path.exists():
                        # Copy new file
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_path, target_path)
                        stats["copied"] += 1
                    elif source_info["mtime"] > target_files[rel_path]["mtime"]:
                        # Update existing file
                        shutil.copy2(source_path, target_path)
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                except Exception:
                    stats["errors"] += 1

            return {
                "message": f"Directory synchronization completed using {sync_type} strategy",
                "source": str(source_full_path),
                "target": str(target_full_path),
                "stats": stats
            }

        except Exception as e:
            return {"error": str(e)}

    def monitor_directory(self, dir_path: str,
                         event_types: Optional[List[str]] = None,
                         exclude_patterns: Optional[List[str]] = None,
                         callback: Optional[callable] = None) -> Dict:
        """Monitor a directory for file system events."""
        try:
            full_path = self.base_dir / dir_path

            # Security checks
            if not self._is_safe_path(full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not full_path.exists() or not full_path.is_dir():
                return {"error": f"Directory not found: {dir_path}"}

            # Set up event handler
            class FileEventHandler(FileSystemEventHandler):
                def __init__(self, tool, callback):
                    self.tool = tool
                    self.callback = callback
                    self.events = []

                def on_any_event(self, event):
                    if not event.is_directory:
                        event_info = {
                            "type": event.event_type,
                            "path": str(Path(event.src_path).relative_to(self.tool.base_dir)),
                            "time": datetime.now().isoformat()
                        }
                        self.events.append(event_info)
                        if self.callback:
                            self.callback(event_info)

            # Initialize observer
            event_handler = FileEventHandler(self, callback)
            observer = Observer()
            observer.schedule(event_handler, str(full_path), recursive=True)
            observer.start()

            return {
                "message": "Directory monitoring started",
                "directory": str(full_path),
                "event_types": event_types or ["all"],
                "exclude_patterns": exclude_patterns,
                "observer": observer,
                "handler": event_handler
            }

        except Exception as e:
            return {"error": str(e)}

    def create_backup(self, source_path: str,
                     backup_dir: str = "backups",
                     backup_type: str = "full",
                     compression: bool = True,
                     max_backups: int = 5) -> Dict:
        """Create a backup of a file or directory."""
        try:
            source_full_path = self.base_dir / source_path
            backup_full_path = self.base_dir / backup_dir

            # Security checks
            if not self._is_safe_path(source_full_path) or not self._is_safe_path(backup_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not source_full_path.exists():
                return {"error": f"Source not found: {source_path}"}

            # Create backup directory if it doesn't exist
            backup_full_path.mkdir(parents=True, exist_ok=True)

            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{source_full_path.name}_{timestamp}"
            if compression:
                backup_name += ".zip"

            backup_path = backup_full_path / backup_name

            # Create backup
            if source_full_path.is_file():
                if compression:
                    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                        zf.write(source_full_path, source_full_path.name)
                else:
                    shutil.copy2(source_full_path, backup_path)
            else:
                if compression:
                    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for root, _, files in os.walk(source_full_path):
                            for file in files:
                                file_path = Path(root) / file
                                arcname = file_path.relative_to(source_full_path)
                                zf.write(file_path, arcname)
                else:
                    shutil.copytree(source_full_path, backup_path)

            # Clean up old backups
            if max_backups > 0:
                backups = sorted(backup_full_path.glob(f"{source_full_path.name}_*"))
                if len(backups) > max_backups:
                    for old_backup in backups[:-max_backups]:
                        old_backup.unlink()

            return {
                "message": f"Backup created successfully",
                "source": str(source_full_path),
                "backup": str(backup_path),
                "type": backup_type,
                "compressed": compression,
                "size": backup_path.stat().st_size,
                "timestamp": timestamp
            }

        except Exception as e:
            return {"error": str(e)}

    def _get_file_list(self, directory: Path, exclude_patterns: Optional[List[str]] = None) -> Dict[str, Dict]:
        """Get a dictionary of files in a directory with their metadata."""
        files = {}
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                file_path = Path(root) / filename
                rel_path = file_path.relative_to(directory)

                # Check if file should be excluded
                if exclude_patterns and any(fnmatch.fnmatch(str(rel_path), pattern) for pattern in exclude_patterns):
                    continue

                if self._is_allowed_file(file_path):
                    files[str(rel_path)] = {
                        "size": file_path.stat().st_size,
                        "mtime": file_path.stat().st_mtime,
                        "type": mimetypes.guess_type(str(file_path))[0] or "text/plain"
                    }
        return files

    def encrypt_file(self, file_path: str, password: str,
                    output_path: Optional[str] = None,
                    delete_original: bool = False) -> Dict:
        """Encrypt a file using Fernet symmetric encryption."""
        try:
            full_path = self.base_dir / file_path

            # Security checks
            if not self._is_safe_path(full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not full_path.exists():
                return {"error": f"File not found: {file_path}"}

            if not self._is_allowed_file(full_path):
                return {"error": f"File type not allowed: {file_path}"}

            # Generate encryption key from password
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            fernet = Fernet(key)

            # Read and encrypt file
            with open(full_path, 'rb') as f:
                file_data = f.read()

            encrypted_data = fernet.encrypt(file_data)

            # Prepare output path
            if output_path:
                output_full_path = self.base_dir / output_path
            else:
                output_full_path = full_path.with_suffix(full_path.suffix + '.enc')

            # Write encrypted file
            with open(output_full_path, 'wb') as f:
                f.write(salt + encrypted_data)

            # Delete original if requested
            if delete_original:
                full_path.unlink()

            return {
                "message": "File encrypted successfully",
                "original": str(full_path),
                "encrypted": str(output_full_path),
                "original_size": len(file_data),
                "encrypted_size": len(encrypted_data) + len(salt),
                "algorithm": "Fernet (AES-128-CBC)",
                "key_derivation": "PBKDF2-HMAC-SHA256"
            }

        except Exception as e:
            return {"error": str(e)}

    def decrypt_file(self, file_path: str, password: str,
                    output_path: Optional[str] = None,
                    delete_encrypted: bool = False) -> Dict:
        """Decrypt an encrypted file."""
        try:
            full_path = self.base_dir / file_path

            # Security checks
            if not self._is_safe_path(full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not full_path.exists():
                return {"error": f"File not found: {file_path}"}

            # Read encrypted file
            with open(full_path, 'rb') as f:
                data = f.read()

            # Extract salt and encrypted data
            salt = data[:16]
            encrypted_data = data[16:]

            # Generate key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            fernet = Fernet(key)

            # Decrypt data
            try:
                decrypted_data = fernet.decrypt(encrypted_data)
            except Exception:
                return {"error": "Decryption failed: Invalid password or corrupted file"}

            # Prepare output path
            if output_path:
                output_full_path = self.base_dir / output_path
            else:
                output_full_path = full_path.with_suffix('').with_suffix('')

            # Write decrypted file
            with open(output_full_path, 'wb') as f:
                f.write(decrypted_data)

            # Delete encrypted file if requested
            if delete_encrypted:
                full_path.unlink()

            return {
                "message": "File decrypted successfully",
                "encrypted": str(full_path),
                "decrypted": str(output_full_path),
                "encrypted_size": len(data),
                "decrypted_size": len(decrypted_data)
            }

        except Exception as e:
            return {"error": str(e)}

    def verify_file_integrity(self, file_path: str,
                            hash_type: str = 'sha256',
                            expected_hash: Optional[str] = None) -> Dict:
        """Verify file integrity using cryptographic hashes."""
        try:
            full_path = self.base_dir / file_path

            # Security checks
            if not self._is_safe_path(full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not full_path.exists():
                return {"error": f"File not found: {file_path}"}

            # Calculate hash
            if hash_type == 'sha256':
                hash_obj = hashlib.sha256()
            elif hash_type == 'sha512':
                hash_obj = hashlib.sha512()
            elif hash_type == 'md5':
                hash_obj = hashlib.md5()
            else:
                return {"error": f"Unsupported hash type: {hash_type}"}

            with open(full_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)

            calculated_hash = hash_obj.hexdigest()

            # Verify if expected hash is provided
            if expected_hash:
                is_valid = calculated_hash.lower() == expected_hash.lower()
                status = "valid" if is_valid else "invalid"
            else:
                is_valid = None
                status = "calculated"

            return {
                "message": f"File integrity {status}",
                "file": str(full_path),
                "size": full_path.stat().st_size,
                "hash_type": hash_type,
                "hash": calculated_hash,
                "expected_hash": expected_hash,
                "is_valid": is_valid
            }

        except Exception as e:
            return {"error": str(e)}

    def create_archive(self, source_path: str,
                      archive_path: Optional[str] = None,
                      format: str = 'zip',
                      compression: str = 'deflate',
                      exclude_patterns: Optional[List[str]] = None) -> Dict:
        """Create an archive of files or directories."""
        try:
            source_full_path = self.base_dir / source_path

            # Security checks
            if not self._is_safe_path(source_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not source_full_path.exists():
                return {"error": f"Source not found: {source_path}"}

            # Prepare archive path
            if archive_path:
                archive_full_path = self.base_dir / archive_path
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_full_path = source_full_path.with_suffix(f'.{format}')

            # Create archive
            if format == 'zip':
                compression_map = {
                    'deflate': zipfile.ZIP_DEFLATED,
                    'bzip2': zipfile.ZIP_BZIP2,
                    'lzma': zipfile.ZIP_LZMA
                }
                comp_method = compression_map.get(compression, zipfile.ZIP_DEFLATED)

                with zipfile.ZipFile(archive_full_path, 'w', comp_method) as zf:
                    if source_full_path.is_file():
                        zf.write(source_full_path, source_full_path.name)
                    else:
                        for root, _, files in os.walk(source_full_path):
                            for file in files:
                                file_path = Path(root) / file
                                if exclude_patterns and any(fnmatch.fnmatch(str(file_path.relative_to(source_full_path)), pattern) for pattern in exclude_patterns):
                                    continue
                                arcname = file_path.relative_to(source_full_path)
                                zf.write(file_path, arcname)

            elif format == 'tar':
                compression_map = {
                    'gzip': 'gz',
                    'bzip2': 'bz2',
                    'lzma': 'xz'
                }
                mode = f'w:{compression_map.get(compression, "gz")}'

                with tarfile.open(archive_full_path, mode) as tf:
                    if source_full_path.is_file():
                        tf.add(source_full_path, source_full_path.name)
                    else:
                        for root, _, files in os.walk(source_full_path):
                            for file in files:
                                file_path = Path(root) / file
                                if exclude_patterns and any(fnmatch.fnmatch(str(file_path.relative_to(source_full_path)), pattern) for pattern in exclude_patterns):
                                    continue
                                arcname = file_path.relative_to(source_full_path)
                                tf.add(file_path, arcname)

            else:
                return {"error": f"Unsupported archive format: {format}"}

            return {
                "message": "Archive created successfully",
                "source": str(source_full_path),
                "archive": str(archive_full_path),
                "format": format,
                "compression": compression,
                "size": archive_full_path.stat().st_size
            }

        except Exception as e:
            return {"error": str(e)}

    def extract_archive(self, archive_path: str,
                       extract_path: Optional[str] = None,
                       password: Optional[str] = None) -> Dict:
        """Extract an archive file."""
        try:
            archive_full_path = self.base_dir / archive_path

            # Security checks
            if not self._is_safe_path(archive_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not archive_full_path.exists():
                return {"error": f"Archive not found: {archive_path}"}

            # Prepare extract path
            if extract_path:
                extract_full_path = self.base_dir / extract_path
            else:
                extract_full_path = archive_full_path.parent / archive_full_path.stem

            # Create extract directory
            extract_full_path.mkdir(parents=True, exist_ok=True)

            # Extract archive
            if archive_full_path.suffix == '.zip':
                with zipfile.ZipFile(archive_full_path, 'r') as zf:
                    if password:
                        zf.setpassword(password.encode())
                    zf.extractall(extract_full_path)

            elif archive_full_path.suffix in ['.tar', '.gz', '.bz2', '.xz']:
                with tarfile.open(archive_full_path, 'r:*') as tf:
                    tf.extractall(extract_full_path)

            else:
                return {"error": f"Unsupported archive format: {archive_full_path.suffix}"}

            return {
                "message": "Archive extracted successfully",
                "archive": str(archive_full_path),
                "extract_path": str(extract_full_path),
                "extracted_files": len(list(extract_full_path.rglob('*')))
            }

        except Exception as e:
            return {"error": str(e)}
