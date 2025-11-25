"""
Document Encryption Service.

Provides AES-256-GCM encryption/decryption for clinical document storage.
Uses random IV for each encryption to ensure semantic security.
"""
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionService:
    """
    AES-256-GCM encryption service for document content.

    Features:
    - AES-256-GCM (Galois/Counter Mode) for authenticated encryption
    - Random 96-bit IV for each encryption (prevents pattern analysis)
    - 128-bit authentication tag (detects tampering)
    - IV prepended to ciphertext for easy decryption

    Ciphertext format: IV (12 bytes) + encrypted_data + auth_tag (16 bytes)

    Example:
        >>> service = EncryptionService.from_env()
        >>> ciphertext = service.encrypt(b"Patient has diabetes")
        >>> plaintext = service.decrypt(ciphertext)
    """

    IV_LENGTH = 12  # 96 bits (recommended for GCM)

    def __init__(self, encryption_key: bytes):
        """
        Initialize encryption service with AES-256 key.

        Args:
            encryption_key: 32-byte (256-bit) encryption key

        Raises:
            ValueError: If key length is not 32 bytes
        """
        if len(encryption_key) != 32:
            raise ValueError(
                f"Encryption key must be 32 bytes (256 bits), got {len(encryption_key)} bytes"
            )

        self.aesgcm = AESGCM(encryption_key)

    @classmethod
    def from_env(cls, key_var: str = "ENCRYPTION_KEY") -> "EncryptionService":
        """
        Create encryption service from environment variable.

        Args:
            key_var: Environment variable name containing hex-encoded key

        Returns:
            EncryptionService instance

        Raises:
            ValueError: If environment variable not set or invalid

        Example:
            >>> # ENCRYPTION_KEY=0123456789abcdef... (64 hex chars)
            >>> service = EncryptionService.from_env()
        """
        key_hex = os.getenv(key_var)
        if not key_hex:
            raise ValueError(f"Environment variable {key_var} not set")

        try:
            key_bytes = bytes.fromhex(key_hex)
        except ValueError as e:
            raise ValueError(f"Invalid hex key in {key_var}: {e}")

        return cls(encryption_key=key_bytes)

    def encrypt(self, plaintext: bytes) -> bytes:
        """
        Encrypt plaintext using AES-256-GCM.

        Args:
            plaintext: Data to encrypt

        Returns:
            Ciphertext with prepended IV: IV || encrypted_data || auth_tag

        Example:
            >>> ciphertext = service.encrypt(b"Confidential patient data")
        """
        # Generate random IV (12 bytes for GCM)
        iv = os.urandom(self.IV_LENGTH)

        # Encrypt plaintext (GCM adds 16-byte auth tag automatically)
        ciphertext_with_tag = self.aesgcm.encrypt(iv, plaintext, associated_data=None)

        # Prepend IV to ciphertext for storage
        return iv + ciphertext_with_tag

    def decrypt(self, ciphertext_with_iv: bytes) -> bytes:
        """
        Decrypt ciphertext using AES-256-GCM.

        Args:
            ciphertext_with_iv: IV || encrypted_data || auth_tag

        Returns:
            Original plaintext

        Raises:
            cryptography.exceptions.InvalidTag: If authentication fails (wrong key or corrupted)

        Example:
            >>> plaintext = service.decrypt(ciphertext)
        """
        # Extract IV from beginning
        iv = ciphertext_with_iv[: self.IV_LENGTH]

        # Extract ciphertext + auth tag
        ciphertext_with_tag = ciphertext_with_iv[self.IV_LENGTH :]

        # Decrypt and verify authentication tag
        plaintext = self.aesgcm.decrypt(iv, ciphertext_with_tag, associated_data=None)

        return plaintext

    @staticmethod
    def generate_key() -> bytes:
        """
        Generate a random 256-bit encryption key.

        Returns:
            32-byte random key

        Example:
            >>> key = EncryptionService.generate_key()
            >>> print(key.hex())  # Print as hex for storage in .env
        """
        return os.urandom(32)
