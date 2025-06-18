import os
import hashlib
import hmac
import base64
from pathlib import Path
from typing import Dict, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from .base import FileOperationsTool

class SecurityOperations(FileOperationsTool):
    def encrypt_file(self, file_path: str, password: str, output_path: Optional[str] = None,
                    delete_original: bool = False) -> Dict:
        """Encrypt a file using Fernet symmetric encryption."""
        try:
            file_full_path = self.base_dir / file_path
            output_full_path = self.base_dir / (output_path or f"{file_path}.enc")

            # Security checks
            if not self._is_safe_path(file_full_path) or not self._is_safe_path(output_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not file_full_path.exists():
                return {"error": "File does not exist"}

            if not self._is_allowed_file(file_full_path):
                return {"error": "File type not allowed"}

            # Generate key from password
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
            with open(file_full_path, 'rb') as f:
                file_data = f.read()

            encrypted_data = fernet.encrypt(file_data)

            # Write encrypted file with salt
            with open(output_full_path, 'wb') as f:
                f.write(salt)
                f.write(encrypted_data)

            # Delete original file if requested
            if delete_original:
                file_full_path.unlink()

            return {
                "message": "File encrypted successfully",
                "original_file": str(file_full_path),
                "encrypted_file": str(output_full_path),
                "original_size": len(file_data),
                "encrypted_size": len(encrypted_data) + len(salt),
                "algorithm": "Fernet (AES-128-CBC)",
                "key_derivation": "PBKDF2-HMAC-SHA256"
            }

        except Exception as e:
            return {"error": str(e)}

    def decrypt_file(self, file_path: str, password: str, output_path: Optional[str] = None,
                    delete_encrypted: bool = False) -> Dict:
        """Decrypt an encrypted file."""
        try:
            file_full_path = self.base_dir / file_path
            output_full_path = self.base_dir / (output_path or file_path[:-4] if file_path.endswith('.enc') else f"{file_path}.dec")

            # Security checks
            if not self._is_safe_path(file_full_path) or not self._is_safe_path(output_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not file_full_path.exists():
                return {"error": "File does not exist"}

            # Read salt and encrypted data
            with open(file_full_path, 'rb') as f:
                salt = f.read(16)
                encrypted_data = f.read()

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
                return {"error": "Decryption failed. Incorrect password or corrupted file."}

            # Write decrypted file
            with open(output_full_path, 'wb') as f:
                f.write(decrypted_data)

            # Delete encrypted file if requested
            if delete_encrypted:
                file_full_path.unlink()

            return {
                "message": "File decrypted successfully",
                "encrypted_file": str(file_full_path),
                "decrypted_file": str(output_full_path),
                "encrypted_size": len(encrypted_data) + len(salt),
                "decrypted_size": len(decrypted_data),
                "algorithm": "Fernet (AES-128-CBC)"
            }

        except Exception as e:
            return {"error": str(e)}

    def verify_file_integrity(self, file_path: str, hash_type: str = 'sha256',
                            expected_hash: Optional[str] = None) -> Dict:
        """Verify the integrity of a file using cryptographic hashes."""
        try:
            file_full_path = self.base_dir / file_path

            # Security checks
            if not self._is_safe_path(file_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not file_full_path.exists():
                return {"error": "File does not exist"}

            # Calculate hash
            hash_obj = hashlib.new(hash_type.lower())
            with open(file_full_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)

            calculated_hash = hash_obj.hexdigest()

            # Verify against expected hash if provided
            is_valid = True
            if expected_hash:
                is_valid = hmac.compare_digest(calculated_hash.lower(), expected_hash.lower())

            return {
                "file": str(file_full_path),
                "hash_type": hash_type,
                "calculated_hash": calculated_hash,
                "expected_hash": expected_hash,
                "is_valid": is_valid,
                "file_size": file_full_path.stat().st_size
            }

        except Exception as e:
            return {"error": str(e)}

    def generate_file_signature(self, file_path: str, key: str, algorithm: str = 'sha256') -> Dict:
        """Generate a cryptographic signature for a file."""
        try:
            file_full_path = self.base_dir / file_path

            # Security checks
            if not self._is_safe_path(file_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not file_full_path.exists():
                return {"error": "File does not exist"}

            # Calculate HMAC
            hmac_obj = hmac.new(
                key.encode(),
                msg=None,
                digestmod=getattr(hashlib, algorithm.lower())
            )

            with open(file_full_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hmac_obj.update(chunk)

            signature = hmac_obj.hexdigest()

            return {
                "file": str(file_full_path),
                "algorithm": algorithm,
                "signature": signature,
                "file_size": file_full_path.stat().st_size
            }

        except Exception as e:
            return {"error": str(e)}

    def verify_file_signature(self, file_path: str, signature: str, key: str,
                            algorithm: str = 'sha256') -> Dict:
        """Verify a file's cryptographic signature."""
        try:
            file_full_path = self.base_dir / file_path

            # Security checks
            if not self._is_safe_path(file_full_path):
                return {"error": "Access denied: Path outside base directory"}

            if not file_full_path.exists():
                return {"error": "File does not exist"}

            # Calculate HMAC
            hmac_obj = hmac.new(
                key.encode(),
                msg=None,
                digestmod=getattr(hashlib, algorithm.lower())
            )

            with open(file_full_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hmac_obj.update(chunk)

            calculated_signature = hmac_obj.hexdigest()
            is_valid = hmac.compare_digest(calculated_signature.lower(), signature.lower())

            return {
                "file": str(file_full_path),
                "algorithm": algorithm,
                "calculated_signature": calculated_signature,
                "provided_signature": signature,
                "is_valid": is_valid,
                "file_size": file_full_path.stat().st_size
            }

        except Exception as e:
            return {"error": str(e)}
