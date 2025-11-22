"""
Encryption Utilities

Provides AES-256 encryption/decryption for sensitive data storage.
Implements key rotation support and secure key management.
"""

import os
import hashlib
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.primitives import hashes


class AES256Encryption:
    """
    AES-256 encryption/decryption with CBC mode and PKCS7 padding.

    This class provides secure encryption for PHI documents stored in PostgreSQL.
    Each document gets a unique IV (Initialization Vector) for security.
    """

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption with master key.

        Args:
            master_key: Master encryption key. If None, uses environment variable.
        """
        self.master_key = master_key or os.environ.get(
            "ENCRYPTION_MASTER_KEY",
            "default-development-key-change-in-production"
        )
        self.backend = default_backend()

    def _derive_key(self, salt: bytes, key_id: str) -> bytes:
        """
        Derive encryption key from master key using PBKDF2.

        Args:
            salt: Salt for key derivation
            key_id: Unique identifier for the key

        Returns:
            32-byte derived key for AES-256
        """
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        key_material = f"{self.master_key}:{key_id}".encode()
        return kdf.derive(key_material)

    def encrypt(self, plaintext: bytes, key_id: str) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt data using AES-256-CBC.

        Args:
            plaintext: Data to encrypt
            key_id: Unique identifier for the encryption key

        Returns:
            Tuple of (encrypted_data, initialization_vector, salt)
        """
        # Generate random salt and IV
        salt = os.urandom(16)
        iv = os.urandom(16)

        # Derive encryption key
        key = self._derive_key(salt, key_id)

        # Apply PKCS7 padding
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext) + padder.finalize()

        # Create cipher and encrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        return ciphertext, iv, salt

    def decrypt(self, ciphertext: bytes, iv: bytes, salt: bytes, key_id: str) -> bytes:
        """
        Decrypt data using AES-256-CBC.

        Args:
            ciphertext: Encrypted data
            iv: Initialization vector used for encryption
            salt: Salt used for key derivation
            key_id: Unique identifier for the encryption key

        Returns:
            Decrypted plaintext
        """
        # Derive encryption key
        key = self._derive_key(salt, key_id)

        # Create cipher and decrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=self.backend
        )
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        # Remove padding
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

        return plaintext

    def compute_hash(self, data: bytes) -> str:
        """
        Compute SHA-256 hash of data for deduplication.

        Args:
            data: Data to hash

        Returns:
            Hex string of SHA-256 hash
        """
        hash_obj = hashlib.sha256()
        hash_obj.update(data)
        return hash_obj.hexdigest()

    def generate_key_id(self, document_id: str) -> str:
        """
        Generate unique key ID for a document.

        Args:
            document_id: Document UUID

        Returns:
            Key ID for encryption
        """
        # In production, this would reference a KMS key
        # For now, we use a simple format
        return f"doc-key-{document_id}"

    def rotate_key(self, old_ciphertext: bytes, old_iv: bytes, old_salt: bytes,
                   old_key_id: str, new_key_id: str) -> Tuple[bytes, bytes, bytes]:
        """
        Rotate encryption key by decrypting with old key and re-encrypting with new key.

        Args:
            old_ciphertext: Data encrypted with old key
            old_iv: IV used with old key
            old_salt: Salt used with old key
            old_key_id: Old key identifier
            new_key_id: New key identifier

        Returns:
            Tuple of (new_ciphertext, new_iv, new_salt)
        """
        # Decrypt with old key
        plaintext = self.decrypt(old_ciphertext, old_iv, old_salt, old_key_id)

        # Re-encrypt with new key
        return self.encrypt(plaintext, new_key_id)


# Global instance for convenience
encryption = AES256Encryption()


def encrypt_document(content: bytes, document_id: str) -> Tuple[bytes, str]:
    """
    Encrypt document content for storage.

    Args:
        content: Document content to encrypt
        document_id: Unique document ID

    Returns:
        Tuple of (encrypted_blob, encryption_metadata)
    """
    key_id = encryption.generate_key_id(document_id)
    ciphertext, iv, salt = encryption.encrypt(content, key_id)

    # Combine ciphertext with IV and salt for storage
    # Format: [salt:16][iv:16][ciphertext:*]
    encrypted_blob = salt + iv + ciphertext

    return encrypted_blob, key_id


def decrypt_document(encrypted_blob: bytes, key_id: str) -> bytes:
    """
    Decrypt document content from storage.

    Args:
        encrypted_blob: Combined encrypted data (salt + iv + ciphertext)
        key_id: Encryption key identifier

    Returns:
        Decrypted document content
    """
    # Extract components
    salt = encrypted_blob[:16]
    iv = encrypted_blob[16:32]
    ciphertext = encrypted_blob[32:]

    return encryption.decrypt(ciphertext, iv, salt, key_id)