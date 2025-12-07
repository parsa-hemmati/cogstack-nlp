"""
Unit tests for Encryption Service.

Tests AES-256-GCM encryption/decryption for clinical document content.
"""

import pytest
from app.services.encryption_service import (
    encrypt_content,
    decrypt_content,
    EncryptionError,
    DecryptionError
)


def test_encrypt_plaintext_returns_ciphertext():
    """Test that encryption returns different ciphertext from plaintext."""
    plaintext = b"This is sensitive patient data"

    ciphertext = encrypt_content(plaintext)

    assert ciphertext != plaintext
    assert len(ciphertext) > len(plaintext)  # Includes IV and auth tag
    assert isinstance(ciphertext, bytes)


def test_decrypt_ciphertext_returns_original_plaintext():
    """Test that decryption returns original plaintext."""
    original_plaintext = b"Patient medical history: diabetes, hypertension"

    # Encrypt
    ciphertext = encrypt_content(original_plaintext)

    # Decrypt
    decrypted_plaintext = decrypt_content(ciphertext)

    assert decrypted_plaintext == original_plaintext


def test_encrypt_same_plaintext_produces_different_ciphertexts():
    """Test that encrypting same plaintext twice produces different ciphertexts (random IV)."""
    plaintext = b"Same content encrypted twice"

    ciphertext1 = encrypt_content(plaintext)
    ciphertext2 = encrypt_content(plaintext)

    # Ciphertexts should be different due to random IV
    assert ciphertext1 != ciphertext2

    # But both should decrypt to same plaintext
    assert decrypt_content(ciphertext1) == plaintext
    assert decrypt_content(ciphertext2) == plaintext


def test_decrypt_with_wrong_key_raises_error(monkeypatch):
    """Test that decryption with wrong key fails."""
    plaintext = b"Secret patient data"

    # Encrypt with current key
    ciphertext = encrypt_content(plaintext)

    # Change the encryption key
    monkeypatch.setenv("ENCRYPTION_KEY", "differentkey123456differentkey123")

    # Decryption should fail with wrong key
    with pytest.raises(DecryptionError) as exc_info:
        decrypt_content(ciphertext)

    assert "Authentication tag verification failed" in str(exc_info.value) or \
           "Decryption failed" in str(exc_info.value)


def test_decrypt_corrupted_ciphertext_raises_error():
    """Test that decryption of corrupted data fails."""
    plaintext = b"Valid data"
    ciphertext = encrypt_content(plaintext)

    # Corrupt the ciphertext
    corrupted_ciphertext = ciphertext[:-10] + b"corrupted!"

    # Decryption should fail
    with pytest.raises(DecryptionError):
        decrypt_content(corrupted_ciphertext)


def test_encrypt_empty_content():
    """Test encrypting empty content."""
    plaintext = b""

    ciphertext = encrypt_content(plaintext)

    assert ciphertext != plaintext
    assert len(ciphertext) > 0  # Should contain IV and auth tag

    decrypted = decrypt_content(ciphertext)
    assert decrypted == plaintext


def test_encrypt_large_content():
    """Test encrypting large content (simulating 50KB RTF file)."""
    plaintext = b"X" * (50 * 1024)  # 50KB

    ciphertext = encrypt_content(plaintext)

    assert len(ciphertext) > len(plaintext)

    decrypted = decrypt_content(ciphertext)
    assert decrypted == plaintext
    assert len(decrypted) == 50 * 1024


def test_encrypt_binary_content():
    """Test encrypting binary content with non-ASCII characters."""
    plaintext = b"\x00\x01\x02\x03\xFF\xFE\xFD\xFC"

    ciphertext = encrypt_content(plaintext)
    decrypted = decrypt_content(ciphertext)

    assert decrypted == plaintext


def test_encrypt_unicode_content():
    """Test encrypting UTF-8 encoded unicode content."""
    plaintext = "Patient notes: café, naïve, résumé 中文".encode('utf-8')

    ciphertext = encrypt_content(plaintext)
    decrypted = decrypt_content(ciphertext)

    assert decrypted == plaintext
    assert decrypted.decode('utf-8') == "Patient notes: café, naïve, résumé 中文"


def test_decrypt_invalid_format_raises_error():
    """Test that decryption of invalid format fails."""
    # Too short (needs at least IV + tag)
    invalid_ciphertext = b"short"

    with pytest.raises(DecryptionError):
        decrypt_content(invalid_ciphertext)


def test_encryption_key_loaded_from_environment(monkeypatch):
    """Test that encryption key is loaded from environment variable."""
    custom_key = "mycustomkey123456mycustomkey1234"
    monkeypatch.setenv("ENCRYPTION_KEY", custom_key)

    plaintext = b"Test with custom key"

    # Should not raise error with valid key
    ciphertext = encrypt_content(plaintext)
    decrypted = decrypt_content(ciphertext)

    assert decrypted == plaintext


def test_encryption_without_key_raises_error(monkeypatch):
    """Test that encryption fails if key is not set."""
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)

    plaintext = b"Test data"

    with pytest.raises(EncryptionError) as exc_info:
        encrypt_content(plaintext)

    assert "ENCRYPTION_KEY" in str(exc_info.value) or "not configured" in str(exc_info.value)


def test_iv_prepended_to_ciphertext():
    """Test that IV (initialization vector) is prepended to ciphertext."""
    plaintext = b"Test content"

    ciphertext = encrypt_content(plaintext)

    # AES-GCM typically uses 12-byte (96-bit) IV
    # IV should be prepended to ciphertext
    assert len(ciphertext) >= 12  # At least IV length

    # Different encryptions of same plaintext should have different IVs
    ciphertext2 = encrypt_content(plaintext)

    # First 12 bytes (IV) should be different
    assert ciphertext[:12] != ciphertext2[:12]


def test_authenticated_encryption_detects_tampering():
    """Test that GCM mode detects ciphertext tampering."""
    plaintext = b"Important patient data"

    ciphertext = encrypt_content(plaintext)

    # Tamper with middle of ciphertext (not IV)
    tampered_ciphertext = bytearray(ciphertext)
    tampered_ciphertext[20] ^= 0xFF  # Flip bits

    # Decryption should fail due to authentication tag mismatch
    with pytest.raises(DecryptionError):
        decrypt_content(bytes(tampered_ciphertext))
