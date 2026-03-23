"""Unit tests for password hashing and JWT creation/verification."""

import uuid
from datetime import timedelta

import pytest
from jose import jwt, JWTError

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """Tests for bcrypt password hashing utilities."""

    def test_hash_password_returns_hash(self):
        hashed = hash_password("testpassword123")
        assert hashed != "testpassword123"
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        hashed = hash_password("mySecurePass!")
        assert verify_password("mySecurePass!", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("mySecurePass!")
        assert verify_password("wrongPassword", hashed) is False

    def test_different_passwords_produce_different_hashes(self):
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")
        assert hash1 != hash2

    def test_same_password_produces_different_hashes(self):
        """bcrypt uses random salt, so same password should hash differently."""
        hash1 = hash_password("samePassword")
        hash2 = hash_password("samePassword")
        assert hash1 != hash2
        # But both should verify
        assert verify_password("samePassword", hash1) is True
        assert verify_password("samePassword", hash2) is True


class TestJWTTokens:
    """Tests for JWT token creation and verification."""

    def test_create_access_token(self):
        user_id = uuid.uuid4()
        token = create_access_token(subject=user_id)
        assert isinstance(token, str)
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"

    def test_create_access_token_with_extra_claims(self):
        user_id = uuid.uuid4()
        token = create_access_token(subject=user_id, extra_claims={"tier": "elite"})
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["tier"] == "elite"

    def test_create_access_token_custom_expiry(self):
        user_id = uuid.uuid4()
        token = create_access_token(subject=user_id, expires_delta=timedelta(hours=2))
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == str(user_id)

    def test_create_refresh_token(self):
        user_id = uuid.uuid4()
        token = create_refresh_token(subject=user_id)
        assert isinstance(token, str)
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"

    def test_decode_token_valid(self):
        user_id = uuid.uuid4()
        token = create_access_token(subject=user_id)
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)

    def test_decode_token_invalid(self):
        with pytest.raises(JWTError):
            decode_token("invalid.token.here")

    def test_decode_token_wrong_secret(self):
        user_id = uuid.uuid4()
        token = jwt.encode(
            {"sub": str(user_id), "type": "access"},
            "wrong-secret",
            algorithm=settings.algorithm,
        )
        with pytest.raises(JWTError):
            decode_token(token)

    def test_access_token_contains_iat(self):
        token = create_access_token(subject=uuid.uuid4())
        payload = decode_token(token)
        assert "iat" in payload
        assert "exp" in payload
