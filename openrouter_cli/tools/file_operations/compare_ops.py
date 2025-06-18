import difflib
from pathlib import Path
from typing import Dict, List, Tuple
from .base import FileOperationsTool

class CompareOperations(FileOperationsTool):
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
