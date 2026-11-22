from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.core.config import Settings

TEST_SETTINGS = Settings(
    _env_file=None,
    jwt_secret="test-secret-that-is-at-least-32-bytes",
    jwt_expire_minutes=15,
)


def test_hash_password_is_not_plain_text():
    hashed = hash_password("correct-horse")

    assert hashed != "correct-horse"
    assert verify_password("correct-horse", hashed)


def test_verify_password_rejects_wrong_password_and_invalid_hash():
    hashed = hash_password("correct-horse")

    assert not verify_password("wrong-password", hashed)
    assert not verify_password("correct-horse", "not-a-bcrypt-hash")


def test_access_token_contains_user_id():
    token = create_access_token(42, settings=TEST_SETTINGS)

    assert decode_access_token(token, TEST_SETTINGS) == 42


def test_expired_access_token_is_rejected():
    token = create_access_token(
        42,
        settings=TEST_SETTINGS,
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(token, TEST_SETTINGS)

    assert exc_info.value.status_code == 401


def test_token_signed_with_another_secret_is_rejected():
    token = create_access_token(42, settings=TEST_SETTINGS)
    other_settings = Settings(
        _env_file=None,
        jwt_secret="another-test-secret-at-least-32-bytes",
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(token, other_settings)

    assert exc_info.value.status_code == 401
