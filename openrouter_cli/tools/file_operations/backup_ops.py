import os
import time
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from .base import FileOperationsTool

class BackupOperations(FileOperationsTool):
    def create_backup(self, source_path: str, backup_dir: str, backup_type: str = 'full',
                     compression: str = 'none', max_backups: int = 5) -> Dict:
        """Create a backup of files or directories."""
        try:
            source_full_path = self.base_dir / source_path
            backup_full_path = self.base_dir / backup_dir

            # Security checks
            if not self._is_safe_path(source_full_path) or not self._is_safe_path(backup_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not source_full_path.exists():
                return {"error": "Source path does not exist"}

            # Create backup directory if it doesn't exist
            backup_full_path.mkdir(parents=True, exist_ok=True)

            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            if backup_type == 'incremental':
                backup_name += "_inc"
            backup_name += ".zip" if compression != 'none' else ""

            backup_file = backup_full_path / backup_name

            # Create backup
            if backup_type == 'full':
                # Full backup - copy everything
                if source_full_path.is_file():
                    shutil.copy2(source_full_path, backup_file)
                else:
                    shutil.make_archive(str(backup_file.with_suffix('')), 'zip', source_full_path)

            elif backup_type == 'incremental':
                # Incremental backup - only copy changed files
                if not source_full_path.is_dir():
                    return {"error": "Incremental backup is only supported for directories"}

                # Get list of files to backup
                files_to_backup = self._get_file_list(source_full_path)

                # Create temporary directory for incremental backup
                temp_dir = backup_full_path / f"temp_{timestamp}"
                temp_dir.mkdir(parents=True, exist_ok=True)

                try:
                    # Copy changed files to temporary directory
                    for file_path, metadata in files_to_backup.items():
                        rel_path = file_path.relative_to(source_full_path)
                        temp_file = temp_dir / rel_path
                        temp_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, temp_file)

                    # Create archive from temporary directory
                    shutil.make_archive(str(backup_file.with_suffix('')), 'zip', temp_dir)
                finally:
                    # Clean up temporary directory
                    shutil.rmtree(temp_dir)
            else:
                return {"error": f"Unsupported backup type: {backup_type}"}

            # Apply compression if specified
            if compression != 'none':
                if compression == 'gzip':
                    with open(backup_file, 'rb') as f_in:
                        with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    backup_file.unlink()
                    backup_file = backup_file.with_suffix('.gz')
                elif compression == 'bzip2':
                    with open(backup_file, 'rb') as f_in:
                        with bz2.open(f"{backup_file}.bz2", 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    backup_file.unlink()
                    backup_file = backup_file.with_suffix('.bz2')
                elif compression == 'lzma':
                    with open(backup_file, 'rb') as f_in:
                        with lzma.open(f"{backup_file}.xz", 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    backup_file.unlink()
                    backup_file = backup_file.with_suffix('.xz')
                else:
                    return {"error": f"Unsupported compression method: {compression}"}

            # Create backup metadata
            metadata = {
                "timestamp": timestamp,
                "backup_type": backup_type,
                "compression": compression,
                "source": str(source_full_path),
                "size": backup_file.stat().st_size,
                "files": len(files_to_backup) if backup_type == 'incremental' else None
            }

            # Save metadata
            metadata_file = backup_file.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            # Clean up old backups if needed
            if max_backups > 0:
                self._cleanup_old_backups(backup_full_path, max_backups)

            return {
                "message": f"Backup created successfully",
                "backup_file": str(backup_file),
                "metadata_file": str(metadata_file),
                "backup_type": backup_type,
                "compression": compression,
                "size": backup_file.stat().st_size,
                "timestamp": timestamp
            }

        except Exception as e:
            return {"error": str(e)}

    def restore_backup(self, backup_path: str, restore_path: str) -> Dict:
        """Restore files from a backup."""
        try:
            backup_full_path = self.base_dir / backup_path
            restore_full_path = self.base_dir / restore_path

            # Security checks
            if not self._is_safe_path(backup_full_path) or not self._is_safe_path(restore_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not backup_full_path.exists():
                return {"error": "Backup file does not exist"}

            # Read metadata if available
            metadata = {}
            metadata_file = backup_full_path.with_suffix('.json')
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

            # Create restore directory if it doesn't exist
            restore_full_path.mkdir(parents=True, exist_ok=True)

            # Restore backup
            if backup_full_path.suffix.lower() == '.zip':
                shutil.unpack_archive(backup_full_path, restore_full_path, 'zip')
            elif backup_full_path.suffix.lower() in ['.gz', '.bz2', '.xz']:
                # Handle compressed backups
                if backup_full_path.suffix.lower() == '.gz':
                    with gzip.open(backup_full_path, 'rb') as f_in:
                        with open(restore_full_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                elif backup_full_path.suffix.lower() == '.bz2':
                    with bz2.open(backup_full_path, 'rb') as f_in:
                        with open(restore_full_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                elif backup_full_path.suffix.lower() == '.xz':
                    with lzma.open(backup_full_path, 'rb') as f_in:
                        with open(restore_full_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
            else:
                # Assume it's a direct file copy
                shutil.copy2(backup_full_path, restore_full_path)

            return {
                "message": "Backup restored successfully",
                "backup_file": str(backup_full_path),
                "restore_path": str(restore_full_path),
                "metadata": metadata
            }

        except Exception as e:
            return {"error": str(e)}

    def list_backups(self, backup_dir: str) -> Dict:
        """List all backups in a directory."""
        try:
            backup_full_path = self.base_dir / backup_dir

            # Security checks
            if not self._is_safe_path(backup_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not backup_full_path.exists():
                return {"error": "Backup directory does not exist"}

            if not backup_full_path.is_dir():
                return {"error": "Path is not a directory"}

            # Get list of backup files
            backups = []
            for file_path in backup_full_path.glob('*'):
                if file_path.suffix.lower() in ['.zip', '.gz', '.bz2', '.xz']:
                    metadata = {}
                    metadata_file = file_path.with_suffix('.json')
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)

                    backups.append({
                        "file": str(file_path),
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime,
                        "metadata": metadata
                    })

            return {
                "backup_dir": str(backup_full_path),
                "backups": sorted(backups, key=lambda x: x["modified"], reverse=True),
                "total_backups": len(backups)
            }

        except Exception as e:
            return {"error": str(e)}

    def _cleanup_old_backups(self, backup_dir: Path, max_backups: int) -> None:
        """Clean up old backups, keeping only the specified number of most recent ones."""
        try:
            # Get list of backup files
            backups = []
            for file_path in backup_dir.glob('*'):
                if file_path.suffix.lower() in ['.zip', '.gz', '.bz2', '.xz']:
                    backups.append((file_path, file_path.stat().st_mtime))

            # Sort by modification time (newest first)
            backups.sort(key=lambda x: x[1], reverse=True)

            # Remove old backups
            for backup_file, _ in backups[max_backups:]:
                backup_file.unlink()
                metadata_file = backup_file.with_suffix('.json')
                if metadata_file.exists():
                    metadata_file.unlink()

        except Exception:
            pass  # Silently fail cleanup
