"""
Tests for JWT authentication service.

Verifies token creation, verification, expiry, and signature validation.
"""

import pytest
from datetime import datetime, timedelta
import uuid
import time

# Add backend to path
import sys
from pathlib import Path
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.auth_service import create_access_token, verify_token
from fastapi import HTTPException


class TestTokenCreation:
    """Test JWT token creation."""

    def test_create_token_returns_dict(self):
        """Test that create_access_token returns a dictionary."""
        # Arrange
        user_id = str(uuid.uuid4())
        role = "clinician"

        # Act
        result = create_access_token(user_id=user_id, role=role)

        # Assert
        assert isinstance(result, dict), \
            "create_access_token should return dict"
        assert "access_token" in result, \
            "Result should contain access_token key"
        assert "token_type" in result, \
            "Result should contain token_type key"

    def test_token_type_is_bearer(self):
        """Test that token type is 'bearer'."""
        # Arrange
        user_id = str(uuid.uuid4())
        role = "admin"

        # Act
        result = create_access_token(user_id=user_id, role=role)

        # Assert
        assert result["token_type"] == "bearer", \
            "Token type should be 'bearer'"

    def test_token_contains_user_id(self):
        """Test that token payload includes user ID (sub claim)."""
        # Arrange
        user_id = str(uuid.uuid4())
        role = "researcher"

        # Act
        result = create_access_token(user_id=user_id, role=role)
        token = result["access_token"]
        payload = verify_token(token)

        # Assert
        assert "sub" in payload, \
            "Token should contain 'sub' (subject) claim"
        assert payload["sub"] == user_id, \
            "Token 'sub' should match user_id"

    def test_token_contains_role(self):
        """Test that token payload includes role."""
        # Arrange
        user_id = str(uuid.uuid4())
        role = "viewer"

        # Act
        result = create_access_token(user_id=user_id, role=role)
        token = result["access_token"]
        payload = verify_token(token)

        # Assert
        assert "role" in payload, \
            "Token should contain 'role' claim"
        assert payload["role"] == role, \
            "Token 'role' should match provided role"

    def test_token_contains_expiry(self):
        """Test that token payload includes expiry (exp claim)."""
        # Arrange
        user_id = str(uuid.uuid4())
        role = "clinician"

        # Act
        result = create_access_token(user_id=user_id, role=role)
        token = result["access_token"]
        payload = verify_token(token)

        # Assert
        assert "exp" in payload, \
            "Token should contain 'exp' (expiry) claim"

        # Verify exp is a future timestamp
        current_time = datetime.utcnow().timestamp()
        assert payload["exp"] > current_time, \
            "Token expiry should be in the future"

    def test_token_contains_issued_at(self):
        """Test that token payload includes issued at (iat claim)."""
        # Arrange
        user_id = str(uuid.uuid4())
        role = "admin"

        # Act
        result = create_access_token(user_id=user_id, role=role)
        token = result["access_token"]
        payload = verify_token(token)

        # Assert
        assert "iat" in payload, \
            "Token should contain 'iat' (issued at) claim"

        # Verify iat is a recent timestamp (within last 5 seconds)
        current_time = datetime.utcnow().timestamp()
        assert abs(payload["iat"] - current_time) < 5, \
            "Token 'iat' should be close to current time"

    def test_token_contains_jti(self):
        """Test that token payload includes JWT ID (jti claim)."""
        # Arrange
        user_id = str(uuid.uuid4())
        role = "clinician"

        # Act
        result = create_access_token(user_id=user_id, role=role)
        token = result["access_token"]
        payload = verify_token(token)

        # Assert
        assert "jti" in payload, \
            "Token should contain 'jti' (JWT ID) claim"

        # Verify jti is a valid UUID
        try:
            uuid.UUID(payload["jti"])
        except ValueError:
            pytest.fail("Token 'jti' should be a valid UUID")

    def test_token_expires_in_8_hours(self):
        """Test that token expires after 8 hours."""
        # Arrange
        user_id = str(uuid.uuid4())
        role = "clinician"
        expected_expiry_hours = 8

        # Act
        result = create_access_token(user_id=user_id, role=role)
        token = result["access_token"]
        payload = verify_token(token)

        # Assert
        current_time = datetime.utcnow().timestamp()
        expected_exp = current_time + (expected_expiry_hours * 3600)
        actual_exp = payload["exp"]

        # Allow 5 second tolerance for test execution time
        assert abs(actual_exp - expected_exp) < 5, \
            f"Token should expire in {expected_expiry_hours} hours"

    def test_each_token_has_unique_jti(self):
        """Test that each token has a unique JWT ID."""
        # Arrange
        user_id = str(uuid.uuid4())
        role = "clinician"

        # Act
        result1 = create_access_token(user_id=user_id, role=role)
        result2 = create_access_token(user_id=user_id, role=role)

        token1 = result1["access_token"]
        token2 = result2["access_token"]

        payload1 = verify_token(token1)
        payload2 = verify_token(token2)

        # Assert
        assert payload1["jti"] != payload2["jti"], \
            "Each token should have unique JWT ID"


class TestTokenVerification:
    """Test JWT token verification."""

    def test_verify_valid_token_returns_payload(self):
        """Test that verify_token returns payload for valid token."""
        # Arrange
        user_id = str(uuid.uuid4())
        role = "researcher"
        result = create_access_token(user_id=user_id, role=role)
        token = result["access_token"]

        # Act
        payload = verify_token(token)

        # Assert
        assert isinstance(payload, dict), \
            "verify_token should return dict"
        assert payload["sub"] == user_id
        assert payload["role"] == role

    def test_verify_expired_token_raises_http_exception(self):
        """Test that verify_token raises HTTPException(401) for expired token."""
        # Arrange
        user_id = str(uuid.uuid4())
        role = "clinician"

        # Create token with -1 hour expiry (already expired)
        result = create_access_token(user_id=user_id, role=role, expires_delta=timedelta(hours=-1))
        token = result["access_token"]

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401, \
            "Expired token should raise HTTP 401"
        assert "expired" in str(exc_info.value.detail).lower(), \
            "Error message should mention expiration"

    def test_verify_invalid_signature_raises_http_exception(self):
        """Test that verify_token raises HTTPException(401) for invalid signature."""
        # Arrange - Create token then modify it (invalid signature)
        user_id = str(uuid.uuid4())
        role = "admin"
        result = create_access_token(user_id=user_id, role=role)
        token = result["access_token"]

        # Tamper with token (change last character)
        tampered_token = token[:-10] + "tampered123"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            verify_token(tampered_token)

        assert exc_info.value.status_code == 401, \
            "Invalid signature should raise HTTP 401"
        assert "invalid" in str(exc_info.value.detail).lower() or \
               "signature" in str(exc_info.value.detail).lower(), \
            "Error message should mention invalid token or signature"

    def test_verify_malformed_token_raises_http_exception(self):
        """Test that verify_token raises HTTPException(401) for malformed token."""
        # Arrange
        malformed_token = "not.a.valid.jwt.token"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            verify_token(malformed_token)

        assert exc_info.value.status_code == 401, \
            "Malformed token should raise HTTP 401"


class TestTokenRoundTrip:
    """Test full token lifecycle (create -> verify)."""

    def test_roundtrip_preserves_all_claims(self):
        """Test that create -> verify preserves all claims."""
        # Arrange
        user_id = str(uuid.uuid4())
        role = "clinician"

        # Act
        result = create_access_token(user_id=user_id, role=role)
        token = result["access_token"]
        payload = verify_token(token)

        # Assert - All required claims present
        required_claims = ["sub", "role", "exp", "iat", "jti"]
        for claim in required_claims:
            assert claim in payload, \
                f"Payload should contain '{claim}' claim"

        # Assert - Claims have correct values
        assert payload["sub"] == user_id
        assert payload["role"] == role


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
