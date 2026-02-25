import json
from datetime import datetime

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import importlib
import sys
import types

from backend import config
from backend.schemas import LocationIn, LoginRequest
from backend.security import create_access_token, hash_password, verify_access_token, verify_password

_BACKEND_MAIN = None
_AUDIT_MODULE = None


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


def _load_audit_with_stubbed_db():
    global _AUDIT_MODULE
    if _AUDIT_MODULE is not None:
        return _AUDIT_MODULE
    stub_db = types.SimpleNamespace(execute=lambda *args, **kwargs: None)
    sys.modules["backend.db"] = stub_db
    _AUDIT_MODULE = importlib.import_module("backend.audit")
    return _AUDIT_MODULE


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


def test_login_writes_audit_event_on_failed_credentials(monkeypatch):
    backend_main = _load_backend_main_with_stubbed_db()
    events = []
    monkeypatch.setattr(backend_main, "API_LOGIN_RATE_LIMIT_ATTEMPTS", 5)
    monkeypatch.setattr(backend_main, "API_LOGIN_RATE_LIMIT_WINDOW_SECONDS", 300)
    monkeypatch.setattr(backend_main, "API_LOGIN_BLOCK_SECONDS", 60)
    monkeypatch.setattr(
        backend_main,
        "fetch_one",
        lambda *_args, **_kwargs: {
            "id": 11,
            "username": "coach1",
            "password_hash": "hash",
            "active": True,
            "role": "coach",
        },
    )
    monkeypatch.setattr(backend_main, "verify_password", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(backend_main, "audit_log_event", lambda **kwargs: events.append(kwargs))
    backend_main._LOGIN_FAILURES.clear()
    backend_main._LOGIN_BLOCKED_UNTIL.clear()

    payload = LoginRequest(username="coach1", password="wrong")
    request = _DummyRequest()
    with pytest.raises(HTTPException):
        backend_main.login(payload, request)

    assert events
    assert events[-1]["action"] == "auth.login"
    assert events[-1]["result"] == "failed"
    assert events[-1]["details"]["reason"] == "invalid_credentials"


def test_login_writes_audit_event_on_success(monkeypatch):
    backend_main = _load_backend_main_with_stubbed_db()
    events = []
    monkeypatch.setattr(
        backend_main,
        "fetch_one",
        lambda *_args, **_kwargs: {
            "id": 21,
            "username": "admin",
            "password_hash": "hash",
            "active": True,
            "role": "admin",
        },
    )
    monkeypatch.setattr(backend_main, "verify_password", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(backend_main, "create_access_token", lambda *_, **__: "token")
    monkeypatch.setattr(backend_main, "audit_log_event", lambda **kwargs: events.append(kwargs))
    backend_main._LOGIN_FAILURES.clear()
    backend_main._LOGIN_BLOCKED_UNTIL.clear()

    payload = LoginRequest(username="admin", password="correct")
    request = _DummyRequest()
    result = backend_main.login(payload, request)

    assert result.access_token == "token"
    assert events
    assert events[-1]["action"] == "auth.login"
    assert events[-1]["result"] == "success"
    assert events[-1]["details"]["role"] == "admin"


def test_locations_create_writes_audit_event(monkeypatch):
    backend_main = _load_backend_main_with_stubbed_db()
    events = []
    monkeypatch.setattr(
        backend_main,
        "_get_user_by_subject",
        lambda _subject: {"id": 7, "username": "admin", "active": True, "role": "admin"},
    )
    monkeypatch.setattr(
        backend_main,
        "execute_returning_one",
        lambda *_args, **_kwargs: {"id": 33, "created_at": "2026-02-25T00:00:00"},
    )
    monkeypatch.setattr(backend_main, "audit_log_event", lambda **kwargs: events.append(kwargs))

    payload = LocationIn(name="HQ", phone=None, address=None)
    result = backend_main.create_location(payload, "admin")

    assert result.id == 33
    assert events
    assert events[-1]["action"] == "locations.create"
    assert events[-1]["resource_type"] == "location"
    assert events[-1]["resource_id"] == "33"


def test_locations_deactivate_writes_audit_event(monkeypatch):
    backend_main = _load_backend_main_with_stubbed_db()
    events = []
    monkeypatch.setattr(
        backend_main,
        "_get_user_by_subject",
        lambda _subject: {"id": 7, "username": "admin", "active": True, "role": "admin"},
    )
    monkeypatch.setattr(
        backend_main,
        "execute_returning_one",
        lambda *_args, **_kwargs: {"id": 33},
    )
    monkeypatch.setattr(backend_main, "audit_log_event", lambda **kwargs: events.append(kwargs))

    result = backend_main.deactivate_location(33, "admin")

    assert result["status"] == "ok"
    assert events
    assert events[-1]["action"] == "locations.deactivate"
    assert events[-1]["resource_type"] == "location"
    assert events[-1]["resource_id"] == "33"


def test_admin_audit_logs_returns_paginated_rows(monkeypatch):
    backend_main = _load_backend_main_with_stubbed_db()
    captured = {"calls": []}

    def _fake_fetch_all(query, params=()):
        captured["calls"].append((query, params))
        if "COUNT(*) AS total" in query:
            return [{"total": 2}]
        return [
            {
                "id": 101,
                "actor_user_id": 7,
                "actor_username": "admin",
                "action": "students.create",
                "resource_type": "student",
                "resource_id": "55",
                "result": "success",
                "ip_address": "127.0.0.1",
                "correlation_id": "cid-1",
                "details": {"name": "John"},
                "created_at": datetime(2026, 2, 25, 10, 0, 0),
            },
            {
                "id": 102,
                "actor_user_id": 7,
                "actor_username": "admin",
                "action": "students.update",
                "resource_type": "student",
                "resource_id": "55",
                "result": "success",
                "ip_address": "127.0.0.1",
                "correlation_id": "cid-2",
                "details": {"name": "John Doe"},
                "created_at": datetime(2026, 2, 25, 10, 5, 0),
            },
        ]

    monkeypatch.setattr(backend_main, "fetch_all", _fake_fetch_all)
    out = backend_main.list_audit_logs(
        "admin",
        date_from="2026-02-25T00:00:00",
        date_to="2026-02-25T23:59:59",
        actor_username="admin",
        action="students",
        resource_type="student",
        result="success",
        limit=10,
        offset=0,
    )

    assert out.total == 2
    assert len(out.rows) == 2
    assert out.rows[0].action == "students.create"
    assert len(captured["calls"]) == 2


def test_admin_audit_logs_uses_limit_and_offset(monkeypatch):
    backend_main = _load_backend_main_with_stubbed_db()
    captured = {"params": []}

    def _fake_fetch_all(query, params=()):
        captured["params"].append(params)
        if "COUNT(*) AS total" in query:
            return [{"total": 0}]
        return []

    monkeypatch.setattr(backend_main, "fetch_all", _fake_fetch_all)
    out = backend_main.list_audit_logs(
        "admin",
        date_from=None,
        date_to=None,
        actor_username="",
        action="",
        resource_type="",
        result="",
        limit=25,
        offset=50,
    )

    assert out.total == 0
    assert out.rows == []
    # second call is data query and includes pagination arguments at the end
    assert captured["params"][1][-2:] == (25, 50)


def test_export_audit_logs_json(monkeypatch):
    backend_main = _load_backend_main_with_stubbed_db()

    def _fake_fetch_all(query, params=()):
        if "COUNT(*) AS total" in query:
            return [{"total": 1}]
        return [
            {
                "id": 900,
                "actor_user_id": 7,
                "actor_username": "admin",
                "action": "users.create",
                "resource_type": "user",
                "resource_id": "88",
                "result": "success",
                "ip_address": "127.0.0.1",
                "correlation_id": "c-1",
                "details": {"username": "john"},
                "created_at": datetime(2026, 2, 25, 11, 0, 0),
            }
        ]

    monkeypatch.setattr(backend_main, "fetch_all", _fake_fetch_all)
    response = backend_main.export_audit_logs(
        "admin",
        format="json",
        date_from=None,
        date_to=None,
        actor_username="",
        action="",
        resource_type="",
        result="",
        limit=100,
        offset=0,
    )

    payload = json.loads(response.body.decode("utf-8"))
    assert payload["total"] == 1
    assert payload["rows"][0]["action"] == "users.create"


def test_export_audit_logs_csv(monkeypatch):
    backend_main = _load_backend_main_with_stubbed_db()

    def _fake_fetch_all(query, params=()):
        if "COUNT(*) AS total" in query:
            return [{"total": 1}]
        return [
            {
                "id": 901,
                "actor_user_id": 7,
                "actor_username": "admin",
                "action": "locations.update",
                "resource_type": "location",
                "resource_id": "44",
                "result": "success",
                "ip_address": "127.0.0.1",
                "correlation_id": "c-2",
                "details": {"name": "HQ"},
                "created_at": datetime(2026, 2, 25, 12, 0, 0),
            }
        ]

    monkeypatch.setattr(backend_main, "fetch_all", _fake_fetch_all)
    response = backend_main.export_audit_logs(
        "admin",
        format="csv",
        date_from=None,
        date_to=None,
        actor_username="",
        action="",
        resource_type="",
        result="",
        limit=100,
        offset=0,
    )

    text = response.body.decode("utf-8")
    assert response.media_type == "text/csv"
    assert "attachment; filename=" in response.headers.get("content-disposition", "")
    assert "action" in text.splitlines()[0]
    assert "locations.update" in text


def test_export_audit_logs_rejects_invalid_format(monkeypatch):
    backend_main = _load_backend_main_with_stubbed_db()
    monkeypatch.setattr(backend_main, "fetch_all", lambda *_args, **_kwargs: [{"total": 0}])

    with pytest.raises(HTTPException) as exc:
        backend_main.export_audit_logs(
            "admin",
            format="xml",
            date_from=None,
            date_to=None,
            actor_username="",
            action="",
            resource_type="",
            result="",
            limit=10,
            offset=0,
        )
    assert exc.value.status_code == 422


def test_build_request_context_prefers_state_correlation_id():
    audit_module = _load_audit_with_stubbed_db()
    class _State:
        correlation_id = "cid-state-1"
        ip_address = "10.0.0.1"

    class _Client:
        host = "127.0.0.1"

    class _Req:
        headers = {"user-agent": "pytest"}
        state = _State()
        client = _Client()

    ctx = audit_module.build_request_context(_Req())
    assert ctx["correlation_id"] == "cid-state-1"
    assert ctx["ip_address"] == "10.0.0.1"


def test_audit_log_event_uses_current_request_context(monkeypatch):
    audit_module = _load_audit_with_stubbed_db()
    captured = {}

    def _fake_execute(_query, params=()):
        captured["params"] = params

    monkeypatch.setattr(audit_module, "execute", _fake_execute)
    audit_module.set_current_request_context(correlation_id="cid-ctx-1", ip_address="192.168.1.1")
    try:
        audit_module.audit_log_event(action="students.update", result="success", details={"k": "v"})
    finally:
        audit_module.clear_current_request_context()

    # params tuple: ..., ip_address, correlation_id, details_json
    assert captured["params"][6] == "192.168.1.1"
    assert captured["params"][7] == "cid-ctx-1"


def test_purge_audit_logs_dry_run(monkeypatch):
    backend_main = _load_backend_main_with_stubbed_db()
    events = []
    called = {"execute_returning_one": False}
    monkeypatch.setattr(
        backend_main,
        "_get_user_by_subject",
        lambda _subject: {"id": 7, "username": "admin", "active": True, "role": "admin"},
    )
    monkeypatch.setattr(backend_main, "fetch_one", lambda *_args, **_kwargs: {"to_delete": 12})
    monkeypatch.setattr(
        backend_main,
        "execute_returning_one",
        lambda *_args, **_kwargs: called.__setitem__("execute_returning_one", True),
    )
    monkeypatch.setattr(backend_main, "audit_log_event", lambda **kwargs: events.append(kwargs))

    out = backend_main.purge_audit_logs("admin", retention_days=90, dry_run=True)

    assert out.dry_run is True
    assert out.retention_days == 90
    assert out.to_delete == 12
    assert out.deleted == 0
    assert called["execute_returning_one"] is False
    assert events[-1]["action"] == "audit.purge.preview"


def test_purge_audit_logs_execute(monkeypatch):
    backend_main = _load_backend_main_with_stubbed_db()
    events = []
    monkeypatch.setattr(
        backend_main,
        "_get_user_by_subject",
        lambda _subject: {"id": 7, "username": "admin", "active": True, "role": "admin"},
    )
    monkeypatch.setattr(backend_main, "fetch_one", lambda *_args, **_kwargs: {"to_delete": 5})
    monkeypatch.setattr(
        backend_main,
        "execute_returning_one",
        lambda *_args, **_kwargs: {"deleted_count": 5},
    )
    monkeypatch.setattr(backend_main, "audit_log_event", lambda **kwargs: events.append(kwargs))

    out = backend_main.purge_audit_logs("admin", retention_days=180, dry_run=False)

    assert out.dry_run is False
    assert out.retention_days == 180
    assert out.to_delete == 5
    assert out.deleted == 5
    assert events[-1]["action"] == "audit.purge"
    assert events[-1]["details"]["deleted"] == 5


def test_audit_log_event_sanitizes_sensitive_and_truncates(monkeypatch):
    audit_module = _load_audit_with_stubbed_db()
    captured = {}

    def _fake_execute(_query, params=()):
        captured["params"] = params

    monkeypatch.setattr(audit_module, "execute", _fake_execute)
    long_value = "x" * 400
    audit_module.audit_log_event(
        action="users.create",
        result="success",
        details={
            "password": "Secret123!",
            "profile": {"token": "abc", "note": long_value},
            "safe": "ok",
        },
    )

    details_json = captured["params"][8]
    payload = json.loads(details_json)
    assert payload["password"] == "***"
    assert payload["profile"]["token"] == "***"
    assert payload["profile"]["note"] == ("x" * 300)
    assert payload["safe"] == "ok"


def test_admin_audit_logs_ignores_whitespace_filters(monkeypatch):
    backend_main = _load_backend_main_with_stubbed_db()
    captured = {"calls": []}

    def _fake_fetch_all(query, params=()):
        captured["calls"].append((query, params))
        if "COUNT(*) AS total" in query:
            return [{"total": 0}]
        return []

    monkeypatch.setattr(backend_main, "fetch_all", _fake_fetch_all)
    out = backend_main.list_audit_logs(
        "admin",
        date_from=None,
        date_to=None,
        actor_username="   ",
        action="   ",
        resource_type="  ",
        result=" ",
        limit=10,
        offset=5,
    )

    assert out.total == 0
    assert out.rows == []
    # no string filters applied -> params for count query should stay empty
    assert captured["calls"][0][1] == ()
    # only pagination params in data query
    assert captured["calls"][1][1] == (10, 5)
