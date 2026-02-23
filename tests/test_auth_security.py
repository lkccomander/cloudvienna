import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import importlib
import sys
import types

from backend import config
from backend.schemas import LoginRequest
from backend.security import create_access_token, hash_password, verify_access_token, verify_password

_BACKEND_MAIN = None


class _DummyClient:
    host = "127.0.0.1"


class _DummyRequest:
    client = _DummyClient()


def _load_backend_main_with_stubbed_db():
    global _BACKEND_MAIN
    if _BACKEND_MAIN is not None:
        return _BACKEND_MAIN
    stub_db = types.SimpleNamespace(
        execute=lambda *args, **kwargs: None,
        execute_returning_one=lambda *args, **kwargs: None,
        fetch_all=lambda *args, **kwargs: [],
        fetch_one=lambda *args, **kwargs: None,
    )
    sys.modules["backend.db"] = stub_db
    _BACKEND_MAIN = importlib.import_module("backend.main")
    return _BACKEND_MAIN


def test_password_hash_roundtrip():
    encoded = hash_password("StrongPwd123!")
    assert verify_password("StrongPwd123!", encoded) is True
    assert verify_password("WrongPwd123!", encoded) is False


def test_verify_access_token_rejects_missing_subject():
    token = jwt.encode({"exp": 9999999999}, config.API_JWT_SECRET, algorithm=config.API_JWT_ALGORITHM)
    with pytest.raises(HTTPException) as exc:
        verify_access_token(token)
    assert exc.value.status_code == 401
    assert "subject" in str(exc.value.detail).lower()


def test_require_auth_checks_active_user(monkeypatch):
    backend_main = _load_backend_main_with_stubbed_db()
    token = create_access_token("activeuser")
    called = {"checked": False}

    def _fake_get_user_by_subject(subject):
        called["checked"] = True
        assert subject == "activeuser"
        return {"username": subject, "active": True}

    monkeypatch.setattr(backend_main, "_get_user_by_subject", _fake_get_user_by_subject)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    subject = backend_main._require_auth(credentials)
    assert subject == "activeuser"
    assert called["checked"] is True


def test_login_rate_limit_blocks_after_repeated_failures(monkeypatch):
    backend_main = _load_backend_main_with_stubbed_db()
    monkeypatch.setattr(backend_main, "API_LOGIN_RATE_LIMIT_ATTEMPTS", 2)
    monkeypatch.setattr(backend_main, "API_LOGIN_RATE_LIMIT_WINDOW_SECONDS", 300)
    monkeypatch.setattr(backend_main, "API_LOGIN_BLOCK_SECONDS", 60)
    monkeypatch.setattr(
        backend_main,
        "fetch_one",
        lambda *_args, **_kwargs: {
            "username": "coach1",
            "password_hash": "hash",
            "active": True,
            "role": "coach",
        },
    )
    monkeypatch.setattr(backend_main, "verify_password", lambda *_args, **_kwargs: False)

    backend_main._LOGIN_FAILURES.clear()
    backend_main._LOGIN_BLOCKED_UNTIL.clear()

    payload = LoginRequest(username="coach1", password="bad-password")
    request = _DummyRequest()

    with pytest.raises(HTTPException) as first:
        backend_main.login(payload, request)
    assert first.value.status_code == 401

    with pytest.raises(HTTPException) as second:
        backend_main.login(payload, request)
    assert second.value.status_code == 401

    with pytest.raises(HTTPException) as third:
        backend_main.login(payload, request)
    assert third.value.status_code == 429


def test_validate_security_settings_prod_rejects_defaults(monkeypatch):
    monkeypatch.setattr(config, "APP_ENV", "prod")
    monkeypatch.setattr(config, "API_JWT_SECRET", "CHANGE_ME_IN_ENV")
    monkeypatch.setattr(config, "API_ADMIN_PASSWORD", "change-me")

    with pytest.raises(RuntimeError):
        config.validate_security_settings()
