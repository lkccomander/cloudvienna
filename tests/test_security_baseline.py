import json
from pathlib import Path

from security.security_baseline import evaluate_security_baseline


def _write_env(path: Path, payload: dict[str, str]) -> None:
    lines = [f'{key}="{value}"' for key, value in payload.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_settings(path: Path, api: dict, db: dict) -> None:
    path.write_text(
        json.dumps({"api": api, "db": db}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def test_prod_flags_http_verify_tls_off_and_weak_db_sslmode(tmp_path):
    backend = tmp_path / "backend"
    backend.mkdir(parents=True, exist_ok=True)
    _write_env(
        backend / ".env.prod",
        {
            "DB_SSLMODE": "prefer",
            "API_JWT_SECRET": "x" * 40,
            "API_ADMIN_PASSWORD": "StrongPass123!",
        },
    )
    _write_settings(
        tmp_path / "app_settings.json",
        api={"base_url": "http://127.0.0.1:8000", "verify_tls": False},
        db={"sslmode": "prefer"},
    )

    report = evaluate_security_baseline("prod", root_dir=tmp_path)
    finding_ids = {item["id"] for item in report["findings"]}

    assert report["status"] == "fail"
    assert "API_URL_NOT_HTTPS" in finding_ids
    assert "API_VERIFY_TLS_DISABLED" in finding_ids
    assert "DB_SSLMODE_WEAK" in finding_ids


def test_prod_passes_when_tls_and_db_ssl_are_strict(tmp_path):
    backend = tmp_path / "backend"
    backend.mkdir(parents=True, exist_ok=True)
    _write_env(
        backend / ".env.prod",
        {
            "DB_SSLMODE": "verify-full",
            "API_JWT_SECRET": "x" * 48,
            "API_ADMIN_PASSWORD": "StrongPass123!",
        },
    )
    _write_settings(
        tmp_path / "app_settings.json",
        api={"base_url": "https://api.example.com", "verify_tls": True},
        db={"sslmode": "verify-full"},
    )

    report = evaluate_security_baseline("prod", root_dir=tmp_path)
    assert report["status"] == "pass"
    assert report["findings_count"] == 0


def test_dev_does_not_enforce_prod_tls_requirements(tmp_path):
    backend = tmp_path / "backend"
    backend.mkdir(parents=True, exist_ok=True)
    _write_env(
        backend / ".env.dev",
        {
            "DB_SSLMODE": "prefer",
            "API_JWT_SECRET": "CHANGE_ME_IN_ENV",
            "API_ADMIN_PASSWORD": "change-me",
        },
    )
    _write_settings(
        tmp_path / "app_settings.json",
        api={"base_url": "http://127.0.0.1:8000", "verify_tls": False},
        db={"sslmode": "prefer"},
    )

    report = evaluate_security_baseline("dev", root_dir=tmp_path)
    finding_ids = {item["id"] for item in report["findings"]}
    assert "API_URL_NOT_HTTPS" not in finding_ids
    assert "API_VERIFY_TLS_DISABLED" not in finding_ids
    assert "DB_SSLMODE_WEAK" not in finding_ids


def test_flags_incomplete_backend_tls_pair_and_malformed_api_host(tmp_path):
    backend = tmp_path / "backend"
    backend.mkdir(parents=True, exist_ok=True)
    _write_env(
        backend / ".env.cloud",
        {
            "DB_SSLMODE": "require",
            "API_HOST": "https://backend.example.com",
            "API_TLS_CERTFILE": "/etc/ssl/cert.pem",
            "API_JWT_SECRET": "x" * 48,
            "API_ADMIN_PASSWORD": "StrongPass123!",
        },
    )
    _write_settings(
        tmp_path / "app_settings.json",
        api={"base_url": "https://api.example.com", "verify_tls": True},
        db={"sslmode": "require"},
    )

    report = evaluate_security_baseline("cloud", root_dir=tmp_path)
    finding_ids = {item["id"] for item in report["findings"]}
    assert "API_TLS_PAIR_INCOMPLETE" in finding_ids
    assert "API_HOST_HAS_SCHEME" in finding_ids
