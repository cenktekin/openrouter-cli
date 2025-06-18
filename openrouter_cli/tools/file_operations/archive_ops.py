import os
import zipfile
import tarfile
import gzip
import bz2
import lzma
from pathlib import Path
from typing import Dict, List, Optional
from .base import FileOperationsTool

class ArchiveOperations(FileOperationsTool):
    def create_archive(self, source_path: str, archive_path: str, format: str = 'zip',
                      compression: str = 'deflate', exclude_patterns: Optional[List[str]] = None) -> Dict:
        """Create an archive of files or directories."""
        try:
            source_full_path = self.base_dir / source_path
            archive_full_path = self.base_dir / archive_path

            # Security checks
            if not self._is_safe_path(source_full_path) or not self._is_safe_path(archive_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not source_full_path.exists():
                return {"error": "Source path does not exist"}

            # Get list of files to archive
            files_to_archive = self._get_file_list(source_full_path, exclude_patterns)

            # Create archive
            if format.lower() == 'zip':
                compression_method = {
                    'deflate': zipfile.ZIP_DEFLATED,
                    'stored': zipfile.ZIP_STORED,
                    'bzip2': zipfile.ZIP_BZIP2,
                    'lzma': zipfile.ZIP_LZMA
                }.get(compression.lower(), zipfile.ZIP_DEFLATED)

                with zipfile.ZipFile(archive_full_path, 'w', compression=compression_method) as archive:
                    for file_path, metadata in files_to_archive.items():
                        archive.write(file_path, file_path.relative_to(source_full_path))

            elif format.lower() == 'tar':
                compression_method = {
                    'none': '',
                    'gzip': 'gz',
                    'bzip2': 'bz2',
                    'lzma': 'xz'
                }.get(compression.lower(), '')

                mode = f'w:{compression_method}' if compression_method else 'w'
                with tarfile.open(archive_full_path, mode) as archive:
                    for file_path, metadata in files_to_archive.items():
                        archive.add(file_path, file_path.relative_to(source_full_path))
            else:
                return {"error": f"Unsupported archive format: {format}"}

            return {
                "message": f"Archive created successfully",
                "source": str(source_full_path),
                "archive": str(archive_full_path),
                "format": format,
                "compression": compression,
                "files_archived": len(files_to_archive),
                "archive_size": archive_full_path.stat().st_size
            }

        except Exception as e:
            return {"error": str(e)}

    def extract_archive(self, archive_path: str, extract_path: str, password: Optional[str] = None) -> Dict:
        """Extract files from an archive."""
        try:
            archive_full_path = self.base_dir / archive_path
            extract_full_path = self.base_dir / extract_path

            # Security checks
            if not self._is_safe_path(archive_full_path) or not self._is_safe_path(extract_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not archive_full_path.exists():
                return {"error": "Archive file does not exist"}

            # Create extraction directory if it doesn't exist
            extract_full_path.mkdir(parents=True, exist_ok=True)

            # Extract archive
            extracted_files = []

            if archive_full_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_full_path, 'r') as archive:
                    if password:
                        archive.setpassword(password.encode())
                    archive.extractall(extract_full_path)
                    extracted_files = archive.namelist()

            elif archive_full_path.suffix.lower() in ['.tar', '.gz', '.bz2', '.xz']:
                with tarfile.open(archive_full_path, 'r:*') as archive:
                    archive.extractall(extract_full_path)
                    extracted_files = archive.getnames()
            else:
                return {"error": f"Unsupported archive format: {archive_full_path.suffix}"}

            return {
                "message": "Archive extracted successfully",
                "archive": str(archive_full_path),
                "extract_path": str(extract_full_path),
                "files_extracted": len(extracted_files),
                "extracted_files": extracted_files
            }

        except Exception as e:
            return {"error": str(e)}

    def compress_file(self, file_path: str, compression: str = 'gzip') -> Dict:
        """Compress a single file using the specified compression method."""
        try:
            file_full_path = self.base_dir / file_path

            # Security checks
            if not self._is_safe_path(file_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not file_full_path.exists():
                return {"error": "File does not exist"}

            if not self._is_allowed_file(file_full_path):
                return {"error": "File type not allowed"}

            # Determine output path based on compression method
            compression_ext = {
                'gzip': '.gz',
                'bzip2': '.bz2',
                'lzma': '.xz'
            }.get(compression.lower(), '.gz')

            output_path = file_full_path.with_suffix(file_full_path.suffix + compression_ext)

            # Compress file
            with open(file_full_path, 'rb') as f_in:
                if compression.lower() == 'gzip':
                    with gzip.open(output_path, 'wb') as f_out:
                        f_out.writelines(f_in)
                elif compression.lower() == 'bzip2':
                    with bz2.open(output_path, 'wb') as f_out:
                        f_out.writelines(f_in)
                elif compression.lower() == 'lzma':
                    with lzma.open(output_path, 'wb') as f_out:
                        f_out.writelines(f_in)
                else:
                    return {"error": f"Unsupported compression method: {compression}"}

            return {
                "message": f"File compressed successfully using {compression}",
                "original_file": str(file_full_path),
                "compressed_file": str(output_path),
                "original_size": file_full_path.stat().st_size,
                "compressed_size": output_path.stat().st_size,
                "compression_ratio": file_full_path.stat().st_size / output_path.stat().st_size
            }

        except Exception as e:
            return {"error": str(e)}

    def decompress_file(self, file_path: str) -> Dict:
        """Decompress a compressed file."""
        try:
            file_full_path = self.base_dir / file_path

            # Security checks
            if not self._is_safe_path(file_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not file_full_path.exists():
                return {"error": "File does not exist"}

            # Determine compression method from file extension
            compression = None
            if file_full_path.suffix.lower() == '.gz':
                compression = 'gzip'
            elif file_full_path.suffix.lower() == '.bz2':
                compression = 'bzip2'
            elif file_full_path.suffix.lower() == '.xz':
                compression = 'lzma'
            else:
                return {"error": "File is not a recognized compressed format"}

            # Determine output path
            output_path = file_full_path.with_suffix('')

            # Decompress file
            with open(output_path, 'wb') as f_out:
                if compression == 'gzip':
                    with gzip.open(file_full_path, 'rb') as f_in:
                        f_out.writelines(f_in)
                elif compression == 'bzip2':
                    with bz2.open(file_full_path, 'rb') as f_in:
                        f_out.writelines(f_in)
                elif compression == 'lzma':
                    with lzma.open(file_full_path, 'rb') as f_in:
                        f_out.writelines(f_in)

            return {
                "message": f"File decompressed successfully",
                "compressed_file": str(file_full_path),
                "decompressed_file": str(output_path),
                "compressed_size": file_full_path.stat().st_size,
                "decompressed_size": output_path.stat().st_size,
                "compression_method": compression
            }

        except Exception as e:
            return {"error": str(e)}
