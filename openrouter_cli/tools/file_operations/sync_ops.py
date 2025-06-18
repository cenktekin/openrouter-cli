import os
import time
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from .base import FileOperationsTool

class SyncOperations(FileOperationsTool):
    def sync_directories(self, source_dir: str, target_dir: str, sync_type: str = 'mirror',
                        exclude_patterns: Optional[List[str]] = None) -> Dict:
        """Synchronize two directories with specified options."""
        try:
            source_full_path = self.base_dir / source_dir
            target_full_path = self.base_dir / target_dir

            # Security checks
            if not self._is_safe_path(source_full_path) or not self._is_safe_path(target_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not source_full_path.exists():
                return {"error": "Source directory does not exist"}

            if not source_full_path.is_dir():
                return {"error": "Source path is not a directory"}

            # Create target directory if it doesn't exist
            target_full_path.mkdir(parents=True, exist_ok=True)

            # Get file lists
            source_files = self._get_file_list(source_full_path, exclude_patterns)
            target_files = self._get_file_list(target_full_path, exclude_patterns)

            # Initialize statistics
            stats = {
                "copied": 0,
                "updated": 0,
                "deleted": 0,
                "skipped": 0,
                "errors": 0
            }

            # Process files based on sync type
            if sync_type == 'mirror':
                # Copy/update files from source to target
                for rel_path, source_meta in source_files.items():
                    target_path = target_full_path / rel_path.relative_to(source_full_path)
                    try:
                        if not target_path.exists():
                            # Copy new file
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(rel_path, target_path)
                            stats["copied"] += 1
                        elif source_meta["modified"] > target_files[target_path]["modified"]:
                            # Update existing file
                            shutil.copy2(rel_path, target_path)
                            stats["updated"] += 1
                        else:
                            stats["skipped"] += 1
                    except Exception:
                        stats["errors"] += 1

                # Delete files in target that don't exist in source
                for target_path in target_files:
                    source_path = source_full_path / target_path.relative_to(target_full_path)
                    if not source_path.exists():
                        try:
                            target_path.unlink()
                            stats["deleted"] += 1
                        except Exception:
                            stats["errors"] += 1

            elif sync_type == 'update':
                # Only copy/update files from source to target
                for rel_path, source_meta in source_files.items():
                    target_path = target_full_path / rel_path.relative_to(source_full_path)
                    try:
                        if not target_path.exists():
                            # Copy new file
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(rel_path, target_path)
                            stats["copied"] += 1
                        elif source_meta["modified"] > target_files[target_path]["modified"]:
                            # Update existing file
                            shutil.copy2(rel_path, target_path)
                            stats["updated"] += 1
                        else:
                            stats["skipped"] += 1
                    except Exception:
                        stats["errors"] += 1
            else:
                return {"error": f"Unsupported sync type: {sync_type}"}

            return {
                "message": f"Directory synchronization completed using {sync_type} strategy",
                "source": str(source_full_path),
                "target": str(target_full_path),
                "sync_type": sync_type,
                "statistics": stats,
                "source_files": len(source_files),
                "target_files": len(target_files)
            }

        except Exception as e:
            return {"error": str(e)}

    def monitor_directory(self, dir_path: str, event_types: List[str] = None,
                         exclude_patterns: Optional[List[str]] = None,
                         callback: Optional[Callable[[Dict], None]] = None) -> Dict:
        """Monitor a directory for file system events."""
        try:
            dir_full_path = self.base_dir / dir_path

            # Security checks
            if not self._is_safe_path(dir_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not dir_full_path.exists():
                return {"error": "Directory does not exist"}

            if not dir_full_path.is_dir():
                return {"error": "Path is not a directory"}

            # Set up event handler
            class EventHandler(FileSystemEventHandler):
                def __init__(self, base_dir: Path, exclude_patterns: Optional[List[str]], callback: Optional[Callable]):
                    self.base_dir = base_dir
                    self.exclude_patterns = exclude_patterns or []
                    self.callback = callback

                def _should_process(self, path: Path) -> bool:
                    if not self.base_dir in path.parents and path != self.base_dir:
                        return False
                    return not any(path.match(pattern) for pattern in self.exclude_patterns)

                def _process_event(self, event: FileSystemEvent):
                    if not self._should_process(Path(event.src_path)):
                        return

                    event_info = {
                        "event_type": event.event_type,
                        "path": event.src_path,
                        "is_directory": event.is_directory,
                        "timestamp": time.time()
                    }

                    if self.callback:
                        self.callback(event_info)

                def on_created(self, event: FileSystemEvent):
                    self._process_event(event)

                def on_modified(self, event: FileSystemEvent):
                    self._process_event(event)

                def on_deleted(self, event: FileSystemEvent):
                    self._process_event(event)

                def on_moved(self, event: FileSystemEvent):
                    self._process_event(event)

            # Set up observer
            event_handler = EventHandler(self.base_dir, exclude_patterns, callback)
            observer = Observer()
            observer.schedule(event_handler, str(dir_full_path), recursive=True)

            # Start monitoring
            observer.start()

            return {
                "message": "Directory monitoring started",
                "directory": str(dir_full_path),
                "event_types": event_types or ["created", "modified", "deleted", "moved"],
                "exclude_patterns": exclude_patterns,
                "has_callback": callback is not None
            }

        except Exception as e:
            return {"error": str(e)}

    def stop_monitoring(self, observer: Observer) -> Dict:
        """Stop directory monitoring."""
        try:
            observer.stop()
            observer.join()

            return {
                "message": "Directory monitoring stopped"
            }

        except Exception as e:
            return {"error": str(e)}

    def get_sync_status(self, source_dir: str, target_dir: str,
                       exclude_patterns: Optional[List[str]] = None) -> Dict:
        """Get the synchronization status between two directories."""
        try:
            source_full_path = self.base_dir / source_dir
            target_full_path = self.base_dir / target_dir

            # Security checks
            if not self._is_safe_path(source_full_path) or not self._is_safe_path(target_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not source_full_path.exists() or not target_full_path.exists():
                return {"error": "One or both directories do not exist"}

            if not source_full_path.is_dir() or not target_full_path.is_dir():
                return {"error": "One or both paths are not directories"}

            # Get file lists
            source_files = self._get_file_list(source_full_path, exclude_patterns)
            target_files = self._get_file_list(target_full_path, exclude_patterns)

            # Analyze differences
            differences = {
                "new_files": [],
                "modified_files": [],
                "deleted_files": [],
                "unchanged_files": []
            }

            # Check for new and modified files
            for rel_path, source_meta in source_files.items():
                target_path = target_full_path / rel_path.relative_to(source_full_path)
                if not target_path.exists():
                    differences["new_files"].append(str(rel_path))
                elif source_meta["modified"] > target_files[target_path]["modified"]:
                    differences["modified_files"].append(str(rel_path))
                else:
                    differences["unchanged_files"].append(str(rel_path))

            # Check for deleted files
            for target_path in target_files:
                source_path = source_full_path / target_path.relative_to(target_full_path)
                if not source_path.exists():
                    differences["deleted_files"].append(str(target_path))

            return {
                "source": str(source_full_path),
                "target": str(target_full_path),
                "source_files": len(source_files),
                "target_files": len(target_files),
                "differences": differences,
                "sync_needed": bool(differences["new_files"] or differences["modified_files"] or differences["deleted_files"])
            }

        except Exception as e:
            return {"error": str(e)}
