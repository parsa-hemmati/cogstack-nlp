"""
Unit tests for Encryption Service.

Tests AES-256-GCM encryption/decryption for document content.
"""
import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.services.encryption_service import EncryptionService


@pytest.fixture
def encryption_service():
    """Create encryption service with test key."""
    # Use a test key (32 bytes for AES-256)
    test_key = b"test_encryption_key_32_bytes!!"  # 32 bytes
    return EncryptionService(encryption_key=test_key)


def test_encrypt_plaintext_returns_ciphertext(encryption_service):
    """Test that encryption produces ciphertext different from plaintext."""
    plaintext = b"This is sensitive patient data."

    ciphertext = encryption_service.encrypt(plaintext)

    assert ciphertext != plaintext
    assert len(ciphertext) > len(plaintext)  # Ciphertext includes IV and tag
    assert isinstance(ciphertext, bytes)


def test_decrypt_ciphertext_returns_original_plaintext(encryption_service):
    """Test that decryption returns the original plaintext."""
    plaintext = b"Confidential clinical notes about patient symptoms."

    ciphertext = encryption_service.encrypt(plaintext)
    decrypted = encryption_service.decrypt(ciphertext)

    assert decrypted == plaintext


def test_different_plaintexts_produce_different_ciphertexts(encryption_service):
    """Test that different plaintexts produce different ciphertexts."""
    plaintext1 = b"Patient A has diabetes."
    plaintext2 = b"Patient B has hypertension."

    ciphertext1 = encryption_service.encrypt(plaintext1)
    ciphertext2 = encryption_service.encrypt(plaintext2)

    assert ciphertext1 != ciphertext2


def test_same_plaintext_produces_different_ciphertexts_with_random_iv(
    encryption_service,
):
    """Test that encrypting the same plaintext twice produces different ciphertexts (due to random IV)."""
    plaintext = b"Same patient data encrypted twice."

    ciphertext1 = encryption_service.encrypt(plaintext)
    ciphertext2 = encryption_service.encrypt(plaintext)

    # Ciphertexts should be different due to random IV
    assert ciphertext1 != ciphertext2

    # But both should decrypt to same plaintext
    assert encryption_service.decrypt(ciphertext1) == plaintext
    assert encryption_service.decrypt(ciphertext2) == plaintext


def test_wrong_key_fails_decryption():
    """Test that decryption with wrong key fails."""
    correct_key = b"correct_key_32_bytes_exactly!!"
    wrong_key = b"wrong_key_32_bytes_exactly_here"

    service_correct = EncryptionService(encryption_key=correct_key)
    service_wrong = EncryptionService(encryption_key=wrong_key)

    plaintext = b"Secret patient information."
    ciphertext = service_correct.encrypt(plaintext)

    # Decryption with wrong key should raise exception
    with pytest.raises(Exception):  # cryptography raises InvalidTag or similar
        service_wrong.decrypt(ciphertext)


def test_corrupted_ciphertext_fails_decryption(encryption_service):
    """Test that corrupted ciphertext fails authentication."""
    plaintext = b"Patient data that will be corrupted."
    ciphertext = encryption_service.encrypt(plaintext)

    # Corrupt the ciphertext by flipping a bit
    corrupted = bytearray(ciphertext)
    corrupted[-1] ^= 0xFF  # Flip last byte
    corrupted = bytes(corrupted)

    # Decryption should fail authentication
    with pytest.raises(Exception):  # InvalidTag or similar
        encryption_service.decrypt(corrupted)


def test_encrypt_empty_plaintext(encryption_service):
    """Test encryption of empty content."""
    plaintext = b""

    ciphertext = encryption_service.encrypt(plaintext)
    decrypted = encryption_service.decrypt(ciphertext)

    assert decrypted == plaintext


def test_encrypt_large_plaintext(encryption_service):
    """Test encryption of large document (50KB)."""
    plaintext = b"A" * 50000  # 50KB clinical document

    ciphertext = encryption_service.encrypt(plaintext)
    decrypted = encryption_service.decrypt(ciphertext)

    assert decrypted == plaintext


def test_iv_prepended_to_ciphertext(encryption_service):
    """Test that IV is prepended to ciphertext for storage."""
    plaintext = b"Test IV prepending."

    ciphertext = encryption_service.encrypt(plaintext)

    # AES-GCM uses 96-bit (12-byte) IV
    # Ciphertext format: IV (12 bytes) + encrypted_data + auth_tag (16 bytes)
    assert len(ciphertext) >= 12 + len(plaintext) + 16


def test_encryption_key_from_environment(monkeypatch):
    """Test that encryption key can be loaded from environment variable."""
    test_key_hex = "0" * 64  # 64 hex chars = 32 bytes
    monkeypatch.setenv("ENCRYPTION_KEY", test_key_hex)

    service = EncryptionService.from_env()
    plaintext = b"Test environment key loading."

    ciphertext = service.encrypt(plaintext)
    decrypted = service.decrypt(ciphertext)

    assert decrypted == plaintext
