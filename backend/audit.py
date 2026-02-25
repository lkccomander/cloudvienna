import json
from contextvars import ContextVar
from typing import Any

from fastapi import Request

from backend.db import execute

_MASKED = "***"
_SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "authorization",
    "secret",
    "jwt",
    "api_key",
}
_MAX_TEXT_LEN = 300
_CURRENT_CORRELATION_ID: ContextVar[str] = ContextVar("audit_correlation_id", default="")
_CURRENT_IP_ADDRESS: ContextVar[str] = ContextVar("audit_ip_address", default="")


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            key_str = str(key)
            if key_str.lower() in _SENSITIVE_KEYS:
                out[key_str] = _MASKED
            else:
                out[key_str] = _sanitize(item)
        return out
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize(item) for item in value]
    if isinstance(value, str):
        return value[:_MAX_TEXT_LEN]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:_MAX_TEXT_LEN]


def build_request_context(request: Request) -> dict[str, str]:
    headers = getattr(request, "headers", {}) or {}
    request_state = getattr(request, "state", None)
    state_correlation = getattr(request_state, "correlation_id", "") if request_state else ""
    correlation_id = state_correlation or headers.get("x-correlation-id") or headers.get("x-request-id") or ""
    state_ip = getattr(request_state, "ip_address", "") if request_state else ""
    ip_address = state_ip or (request.client.host if request.client else "unknown")
    return {
        "ip_address": ip_address,
        "correlation_id": correlation_id,
        "user_agent": headers.get("user-agent", "")[:_MAX_TEXT_LEN],
    }


def set_current_request_context(*, correlation_id: str, ip_address: str) -> None:
    _CURRENT_CORRELATION_ID.set((correlation_id or "").strip())
    _CURRENT_IP_ADDRESS.set((ip_address or "").strip())


def clear_current_request_context() -> None:
    _CURRENT_CORRELATION_ID.set("")
    _CURRENT_IP_ADDRESS.set("")


def get_current_request_context() -> dict[str, str]:
    return {
        "correlation_id": _CURRENT_CORRELATION_ID.get(""),
        "ip_address": _CURRENT_IP_ADDRESS.get(""),
    }


def audit_log_event(
    *,
    action: str,
    result: str,
    actor_user_id: int | None = None,
    actor_username: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    correlation_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    payload = _sanitize(details or {})
    current = get_current_request_context()
    resolved_ip = ip_address or current.get("ip_address")
    resolved_correlation = correlation_id or current.get("correlation_id")
    try:
        execute(
            """
            INSERT INTO audit_log (
                actor_user_id,
                actor_username,
                action,
                resource_type,
                resource_id,
                result,
                ip_address,
                correlation_id,
                details,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, now())
            """,
            (
                actor_user_id,
                (actor_username or "").strip() or None,
                action,
                resource_type,
                resource_id,
                result,
                (resolved_ip or "").strip() or None,
                (resolved_correlation or "").strip() or None,
                json.dumps(payload, ensure_ascii=True),
            ),
        )
    except Exception:
        # Audit must not block business requests.
        return
