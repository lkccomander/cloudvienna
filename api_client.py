import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


class ApiError(Exception):
    pass


def _resolve_settings_path():
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "app_settings.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_settings.json")


def _load_settings():
    try:
        with open(_resolve_settings_path(), "r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _api_config():
    cfg = _load_settings().get("api", {})
    if not isinstance(cfg, dict):
        cfg = {}
    base_url = os.getenv("API_BASE_URL") or cfg.get("base_url")
    username = os.getenv("API_USER") or cfg.get("username")
    password = os.getenv("API_PASSWORD") or cfg.get("password")
    return {
        "base_url": (base_url or "").rstrip("/"),
        "username": username or "",
        "password": password or "",
    }


def is_api_configured():
    cfg = _api_config()
    return bool(cfg["base_url"] and cfg["username"] and cfg["password"])


_TOKEN = None
_TOKEN_EXP = 0


def _request(method, path, payload=None, token=None):
    cfg = _api_config()
    if not cfg["base_url"]:
        raise ApiError("API base_url is not configured in app_settings.json (api.base_url).")
    url = f"{cfg['base_url']}{path}"

    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url=url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            body = resp.read().decode("utf-8") if resp.length != 0 else ""
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        detail = raw
        try:
            parsed = json.loads(raw)
            detail = parsed.get("detail", raw)
        except Exception:
            pass
        raise ApiError(f"API {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ApiError(f"Cannot reach API server: {exc.reason}") from exc


def _login():
    cfg = _api_config()
    if not cfg["username"] or not cfg["password"]:
        raise ApiError("API username/password are not configured in app_settings.json (api.username/api.password).")
    response = _request(
        "POST",
        "/auth/login",
        payload={"username": cfg["username"], "password": cfg["password"]},
    )
    token = response.get("access_token")
    if not token:
        raise ApiError("API login did not return access_token.")
    expires_minutes = int(response.get("expires_in_minutes", 60))
    return token, time.time() + (expires_minutes * 60)


def _ensure_token(force_refresh=False):
    global _TOKEN, _TOKEN_EXP
    if not force_refresh and _TOKEN and (_TOKEN_EXP - 10) > time.time():
        return _TOKEN
    _TOKEN, _TOKEN_EXP = _login()
    return _TOKEN


def _with_auth_request(method, path, payload=None):
    token = _ensure_token(force_refresh=False)
    try:
        return _request(method, path, payload=payload, token=token)
    except ApiError as exc:
        if "API 401:" not in str(exc):
            raise
    token = _ensure_token(force_refresh=True)
    return _request(method, path, payload=payload, token=token)


def list_students(limit, offset, status_filter):
    params = urllib.parse.urlencode(
        {"limit": int(limit), "offset": int(offset), "status_filter": status_filter}
    )
    return _with_auth_request("GET", f"/students/list?{params}")


def count_students(status_filter):
    params = urllib.parse.urlencode({"status_filter": status_filter})
    return _with_auth_request("GET", f"/students/count?{params}")


def create_student(payload):
    return _with_auth_request("POST", "/students/create", payload=payload)


def get_student(student_id):
    return _with_auth_request("GET", f"/students/{int(student_id)}")


def update_student(student_id, payload):
    return _with_auth_request("PUT", f"/students/{int(student_id)}", payload=payload)


def deactivate_student(student_id):
    return _with_auth_request("POST", f"/students/{int(student_id)}/deactivate")


def reactivate_student(student_id):
    return _with_auth_request("POST", f"/students/{int(student_id)}/reactivate")


def active_locations():
    return _with_auth_request("GET", "/locations/active")
