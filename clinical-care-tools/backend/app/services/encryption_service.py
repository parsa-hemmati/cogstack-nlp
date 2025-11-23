"""
Encryption Service for Clinical Document Content.

Provides AES-256-GCM encryption and decryption for protecting PHI in stored documents.
Uses authenticated encryption to ensure both confidentiality and integrity.

Security Features:
- AES-256-GCM (Galois/Counter Mode) for authenticated encryption
- Random 96-bit initialization vector (IV) for each encryption
- 128-bit authentication tag for integrity verification
- Encryption key loaded from environment variable
- FIPS 140-2 compliant cryptography (via cryptography library)

Usage:
    >>> from app.services.encryption_service import encrypt_content, decrypt_content
    >>>
    >>> # Encrypt document content
    >>> plaintext = b"Patient medical history..."
    >>> ciphertext = encrypt_content(plaintext)
    >>>
    >>> # Decrypt document content
    >>> decrypted = decrypt_content(ciphertext)
    >>> assert decrypted == plaintext

Environment Variables:
    ENCRYPTION_KEY: 32-character base64-encoded AES-256 key
                    Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
"""

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
import secrets


class EncryptionError(Exception):
    """Raised when encryption fails."""
    pass


class DecryptionError(Exception):
    """Raised when decryption fails."""
    pass


def _get_encryption_key() -> bytes:
    """
    Load encryption key from environment variable.

    Returns:
        bytes: 32-byte (256-bit) encryption key

    Raises:
        EncryptionError: If ENCRYPTION_KEY is not set or invalid

    Environment:
        ENCRYPTION_KEY: 32-character string (will be encoded to bytes)
    """
    key_str = os.getenv("ENCRYPTION_KEY")

    if not key_str:
        raise EncryptionError(
            "ENCRYPTION_KEY environment variable not configured. "
            "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )

    # Encode string to bytes and pad/truncate to 32 bytes
    key_bytes = key_str.encode('utf-8')

    if len(key_bytes) < 32:
        # Pad with zeros if too short
        key_bytes = key_bytes.ljust(32, b'\x00')
    elif len(key_bytes) > 32:
        # Truncate if too long
        key_bytes = key_bytes[:32]

    return key_bytes


def encrypt_content(plaintext: bytes) -> bytes:
    """
    Encrypt content using AES-256-GCM.

    Args:
        plaintext: Raw content to encrypt (bytes)

    Returns:
        bytes: Encrypted content with format: IV || ciphertext || auth_tag
              IV is 12 bytes (96 bits)
              Auth tag is 16 bytes (128 bits)

    Raises:
        EncryptionError: If encryption fails or key is not configured

    Example:
        >>> plaintext = b"Sensitive patient data"
        >>> ciphertext = encrypt_content(plaintext)
        >>> len(ciphertext) > len(plaintext)  # Includes IV and tag
        True
    """
    try:
        # Get encryption key
        key = _get_encryption_key()

        # Create AESGCM cipher
        aesgcm = AESGCM(key)

        # Generate random 96-bit IV (nonce)
        # NIST recommends 96-bit IV for GCM
        iv = secrets.token_bytes(12)

        # Encrypt and authenticate
        # GCM mode produces: ciphertext || authentication_tag
        ciphertext_with_tag = aesgcm.encrypt(iv, plaintext, None)

        # Return: IV || ciphertext || tag
        return iv + ciphertext_with_tag

    except EncryptionError:
        # Re-raise encryption errors
        raise
    except Exception as e:
        raise EncryptionError(f"Encryption failed: {str(e)}")


def decrypt_content(ciphertext: bytes) -> bytes:
    """
    Decrypt content encrypted with AES-256-GCM.

    Args:
        ciphertext: Encrypted content with format: IV || ciphertext || auth_tag

    Returns:
        bytes: Original plaintext content

    Raises:
        DecryptionError: If decryption fails, authentication fails, or format is invalid

    Example:
        >>> ciphertext = encrypt_content(b"Secret data")
        >>> plaintext = decrypt_content(ciphertext)
        >>> plaintext
        b'Secret data'
    """
    try:
        # Verify minimum length: IV (12) + tag (16) = 28 bytes
        if len(ciphertext) < 28:
            raise DecryptionError(
                f"Invalid ciphertext format: too short (got {len(ciphertext)} bytes, need at least 28)"
            )

        # Get encryption key
        key = _get_encryption_key()

        # Create AESGCM cipher
        aesgcm = AESGCM(key)

        # Extract IV (first 12 bytes)
        iv = ciphertext[:12]

        # Extract ciphertext + tag (remaining bytes)
        ciphertext_with_tag = ciphertext[12:]

        # Decrypt and verify authentication tag
        # Will raise exception if authentication fails
        plaintext = aesgcm.decrypt(iv, ciphertext_with_tag, None)

        return plaintext

    except DecryptionError:
        # Re-raise decryption errors
        raise
    except Exception as e:
        # Catch authentication failures and other errors
        if "Authentication tag verification failed" in str(e) or \
           "MAC check failed" in str(e):
            raise DecryptionError("Authentication tag verification failed: content may be corrupted or tampered")
        else:
            raise DecryptionError(f"Decryption failed: {str(e)}")


def generate_encryption_key() -> str:
    """
    Generate a new random encryption key for AES-256.

    Returns:
        str: 32-character URL-safe base64-encoded key

    Example:
        >>> key = generate_encryption_key()
        >>> len(key)
        32
        >>> # Set in environment: export ENCRYPTION_KEY="<key>"
    """
    return secrets.token_urlsafe(32)[:32]


# Module-level docstring test
if __name__ == "__main__":
    # Example usage
    print("Encryption Service Example")
    print("-" * 50)

    # Generate key
    key = generate_encryption_key()
    print(f"Generated key: {key}")
    print(f"Set environment: export ENCRYPTION_KEY='{key}'")
    print()

    # Set key for demonstration
    os.environ["ENCRYPTION_KEY"] = key

    # Encrypt
    plaintext = b"Patient ID: 12345, Diagnosis: Hypertension"
    print(f"Plaintext: {plaintext}")

    ciphertext = encrypt_content(plaintext)
    print(f"Ciphertext: {ciphertext[:50]}... ({len(ciphertext)} bytes)")

    # Decrypt
    decrypted = decrypt_content(ciphertext)
    print(f"Decrypted: {decrypted}")

    # Verify
    print(f"Decryption successful: {decrypted == plaintext}")
