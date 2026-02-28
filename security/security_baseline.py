#!/usr/bin/env python3
"""Security baseline checks for CloudVienna (Pentest Baseline v1)."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
VALID_ENVS = {"dev", "prod", "cloud"}
PROD_LIKE_ENVS = {"prod", "cloud"}
STRICT_DB_SSLMODES = {"require", "verify-ca", "verify-full"}


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


def _load_effective_env(root_dir: Path, env_name: str) -> tuple[dict[str, str], list[Path]]:
    backend_dir = root_dir / "backend"
    variant = _env_variant(env_name)
    ordered = [backend_dir / ".env", backend_dir / variant]
    merged: dict[str, str] = {}
    present: list[Path] = []
    for env_file in ordered:
        if env_file.exists():
            present.append(env_file)
        merged.update(_parse_env_file(env_file))
    return merged, present


def _load_settings(root_dir: Path) -> dict[str, Any]:
    settings_path = root_dir / "app_settings.json"
    if not settings_path.exists():
        return {}
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _add_finding(findings: list[dict[str, str]], finding_id: str, severity: str, title: str, detail: str) -> None:
    findings.append(
        {
            "id": finding_id,
            "severity": severity,
            "title": title,
            "detail": detail,
        }
    )


def evaluate_security_baseline(env_name: str, root_dir: Path | None = None) -> dict[str, Any]:
    env_name = (env_name or "").strip().lower()
    if env_name not in VALID_ENVS:
        raise ValueError(f"Invalid env '{env_name}'. Use one of: dev, prod, cloud.")

    base_dir = (root_dir or ROOT_DIR).resolve()
    env_values, env_files = _load_effective_env(base_dir, env_name)
    settings = _load_settings(base_dir)
    api_cfg = settings.get("api") if isinstance(settings.get("api"), dict) else {}
    db_cfg = settings.get("db") if isinstance(settings.get("db"), dict) else {}
    findings: list[dict[str, str]] = []

    base_url = str(api_cfg.get("base_url", "")).strip()
    verify_tls = _parse_bool(api_cfg.get("verify_tls", True))
    db_sslmode = str(env_values.get("DB_SSLMODE") or db_cfg.get("sslmode") or "prefer").strip().lower()
    api_host = str(env_values.get("API_HOST", "")).strip()

    if not env_files:
        _add_finding(
            findings,
            "ENV_FILES_MISSING",
            "high",
            "No backend env files found",
            "Expected backend/.env and/or backend/.env.<env> to exist for deterministic security config.",
        )

    if not base_url:
        _add_finding(
            findings,
            "API_BASE_URL_MISSING",
            "high",
            "API base URL is missing",
            "app_settings.json api.base_url is required.",
        )

    if env_name in PROD_LIKE_ENVS:
        if base_url and not base_url.lower().startswith("https://"):
            _add_finding(
                findings,
                "API_URL_NOT_HTTPS",
                "critical",
                "API base URL is not HTTPS in prod/cloud",
                f"Current value: {base_url}. Use an HTTPS endpoint and valid certificate chain.",
            )

        if not verify_tls:
            _add_finding(
                findings,
                "API_VERIFY_TLS_DISABLED",
                "critical",
                "TLS verification disabled in prod/cloud",
                "Set app_settings.json api.verify_tls=true and use trusted certificates or ca_file.",
            )

        if db_sslmode not in STRICT_DB_SSLMODES:
            _add_finding(
                findings,
                "DB_SSLMODE_WEAK",
                "high",
                "DB SSL mode is weak in prod/cloud",
                f"Current DB_SSLMODE='{db_sslmode}'. Recommended: require, verify-ca, or verify-full.",
            )

    certfile = str(env_values.get("API_TLS_CERTFILE", "")).strip()
    keyfile = str(env_values.get("API_TLS_KEYFILE", "")).strip()
    if bool(certfile) ^ bool(keyfile):
        _add_finding(
            findings,
            "API_TLS_PAIR_INCOMPLETE",
            "medium",
            "Backend TLS cert/key pair is incomplete",
            "Both API_TLS_CERTFILE and API_TLS_KEYFILE must be set together (or both empty when using a TLS proxy).",
        )

    if api_host.lower().startswith(("http://", "https://")):
        _add_finding(
            findings,
            "API_HOST_HAS_SCHEME",
            "medium",
            "API_HOST includes URL scheme",
            f"Current API_HOST='{api_host}'. Use a bind host/IP only (e.g., 0.0.0.0 or 127.0.0.1); keep URLs in app_settings.json api.base_url.",
        )

    jwt_secret = str(env_values.get("API_JWT_SECRET", "")).strip()
    admin_password = str(env_values.get("API_ADMIN_PASSWORD", "")).strip()
    if env_name in PROD_LIKE_ENVS:
        if jwt_secret == "CHANGE_ME_IN_ENV" or len(jwt_secret) < 32:
            _add_finding(
                findings,
                "JWT_SECRET_WEAK",
                "critical",
                "API_JWT_SECRET is weak/default",
                "Set a non-default secret with at least 32 characters.",
            )
        if admin_password == "change-me" or len(admin_password) < 12:
            _add_finding(
                findings,
                "ADMIN_PASSWORD_WEAK",
                "critical",
                "API_ADMIN_PASSWORD is weak/default",
                "Set a non-default password with at least 12 characters.",
            )

    severity_weight = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    highest = max((severity_weight[item["severity"]] for item in findings), default=0)
    status = "pass" if highest <= 1 else "fail"

    return {
        "env": env_name,
        "status": status,
        "findings_count": len(findings),
        "findings": findings,
        "context": {
            "root_dir": str(base_dir),
            "env_files": [str(path) for path in env_files],
            "backend_api_host": api_host,
            "api_base_url": base_url,
            "api_verify_tls": verify_tls,
            "db_sslmode": db_sslmode,
        },
    }


def _render_text(report: dict[str, Any]) -> str:
    lines = [
        f"[SECURITY_BASELINE] env={report['env']} status={report['status']} findings={report['findings_count']}",
        f"- backend_api_host={report['context']['backend_api_host'] or '(missing)'}",
        f"- api_base_url={report['context']['api_base_url'] or '(missing)'}",
        f"- api_verify_tls={report['context']['api_verify_tls']}",
        f"- db_sslmode={report['context']['db_sslmode']}",
    ]
    if report["context"]["env_files"]:
        lines.append("- env_files=" + ", ".join(report["context"]["env_files"]))
    else:
        lines.append("- env_files=(none)")

    if not report["findings"]:
        lines.append("No findings.")
        return "\n".join(lines)

    lines.append("Findings:")
    for item in report["findings"]:
        lines.append(f"- [{item['severity'].upper()}] {item['id']}: {item['title']}")
        lines.append(f"  {item['detail']}")
    return "\n".join(lines)


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Security Baseline Report",
        "",
        f"- Environment: `{report['env']}`",
        f"- Status: `{report['status']}`",
        f"- Findings: `{report['findings_count']}`",
        "",
        "## Context",
        f"- Backend API host: `{report['context']['backend_api_host'] or '(missing)'}`",
        f"- API base URL: `{report['context']['api_base_url'] or '(missing)'}`",
        f"- API verify TLS: `{report['context']['api_verify_tls']}`",
        f"- DB SSL mode: `{report['context']['db_sslmode']}`",
    ]
    if report["context"]["env_files"]:
        lines.append(f"- Env files: `{', '.join(report['context']['env_files'])}`")
    else:
        lines.append("- Env files: `(none)`")

    lines.append("")
    lines.append("## Findings")
    if not report["findings"]:
        lines.append("- No findings.")
    else:
        for item in report["findings"]:
            lines.append(f"- **{item['severity'].upper()}** `{item['id']}`: {item['title']}")
            lines.append(f"  - {item['detail']}")
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CloudVienna security baseline checks.")
    parser.add_argument("--env", choices=["dev", "prod", "cloud"], default=os.getenv("APP_ENV", "dev"))
    parser.add_argument("--format", choices=["text", "json", "md"], default="text")
    parser.add_argument("--output", help="Optional output file path.")
    parser.add_argument(
        "--fail-on",
        choices=["none", "medium", "high", "critical"],
        default="high",
        help="Exit non-zero when findings at or above this severity are present.",
    )
    return parser.parse_args()


def _should_fail(report: dict[str, Any], fail_on: str) -> bool:
    if fail_on == "none":
        return False
    threshold = {"medium": 2, "high": 3, "critical": 4}[fail_on]
    severity_weight = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    return any(severity_weight[item["severity"]] >= threshold for item in report["findings"])


def main() -> int:
    args = _parse_args()
    report = evaluate_security_baseline(args.env)

    if args.format == "json":
        rendered = json.dumps(report, indent=2, ensure_ascii=False)
    elif args.format == "md":
        rendered = _render_markdown(report)
    else:
        rendered = _render_text(report)

    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")

    return 1 if _should_fail(report, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
