#!/usr/bin/env python3
"""Validate backend/client bootstrap config before starting the API."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate cloudvienna runtime configuration.")
    parser.add_argument("--env", choices=["dev", "prod", "cloud"], default="dev")
    return parser.parse_args()


def _env_variant(env_name: str) -> str:
    return {"dev": ".env.dev", "prod": ".env.prod", "cloud": ".env.cloud"}.get(env_name, ".env")


def _parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    parsed: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        parsed[key.strip()] = value.strip().strip('"').strip("'")
    return parsed


def _load_effective_env(env_name: str) -> tuple[dict[str, str], list[Path]]:
    variant = _env_variant(env_name)
    ordered = [
        BACKEND_DIR / ".env",
        BACKEND_DIR / variant,
    ]
    merged: dict[str, str] = {}
    present: list[Path] = []
    for env_file in ordered:
        if env_file.exists():
            present.append(env_file)
        merged.update(_parse_env_file(env_file))
    return merged, present


def _load_settings() -> dict:
    settings_path = ROOT_DIR / "app_settings.json"
    if not settings_path.exists():
        return {}
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _has_text(value: object) -> bool:
    return bool(str(value or "").strip())


def main() -> int:
    args = _parse_args()
    env_values, env_files = _load_effective_env(args.env)
    settings = _load_settings()
    errors: list[str] = []

    if not env_files:
        errors.append("No env files found (.env*).")

    required_env = [
        "DB_USER",
        "DB_PASSWORD",
        "API_ADMIN_USER",
        "API_ADMIN_PASSWORD",
        "API_JWT_SECRET",
    ]
    for key in required_env:
        if not _has_text(env_values.get(key)):
            errors.append(f"Missing required env key: {key}")

    db_cfg = settings.get("db")
    api_cfg = settings.get("api")
    if not isinstance(db_cfg, dict):
        errors.append("app_settings.json missing object: db")
    else:
        for key in ("host", "name", "port"):
            if not _has_text(db_cfg.get(key)):
                errors.append(f"app_settings.json db.{key} is required")
    if not isinstance(api_cfg, dict):
        errors.append("app_settings.json missing object: api")
    else:
        for key in ("base_url", "username", "password"):
            if not _has_text(api_cfg.get(key)):
                errors.append(f"app_settings.json api.{key} is required")

    if args.env in {"prod", "cloud"}:
        jwt_secret = str(env_values.get("API_JWT_SECRET", "")).strip()
        admin_password = str(env_values.get("API_ADMIN_PASSWORD", "")).strip()
        if jwt_secret == "CHANGE_ME_IN_ENV" or len(jwt_secret) < 32:
            errors.append("API_JWT_SECRET must be non-default and >= 32 chars in prod/cloud")
        if admin_password == "change-me" or len(admin_password) < 12:
            errors.append("API_ADMIN_PASSWORD must be non-default and >= 12 chars in prod/cloud")

    if errors:
        print("[CONFIG] Validation failed:")
        for item in errors:
            print(f"- {item}")
        return 1

    print("[CONFIG] Validation OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
