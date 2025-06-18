import os
import re
import fnmatch
import binascii
from pathlib import Path
from typing import Dict, List, Optional
from .base import FileOperationsTool

class SearchOperations(FileOperationsTool):
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
