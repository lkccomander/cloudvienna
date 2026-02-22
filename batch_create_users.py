import argparse
import json
import sys

from api_client import ApiError, batch_create_api_users


def _load_json(path: str):
    with open(path, "r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list of objects.")
    return data


def _username_from_row(row: dict) -> str:
    username = str(row.get("username", "")).strip()
    if username:
        return username
    email = str(row.get("email", "")).strip()
    if "@" in email:
        return email.split("@", 1)[0].strip()
    return ""


def _normalize_users(items: list[dict], default_role: str, default_password: str) -> list[dict]:
    users = []
    for idx, row in enumerate(items, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Row {idx}: expected object.")

        username = _username_from_row(row)
        password = str(row.get("password", "")).strip() or default_password
        role = str(row.get("role", default_role)).strip() or default_role

        if not username:
            raise ValueError(f"Row {idx}: missing username.")
        if not password:
            raise ValueError(
                f"Row {idx}: missing password (provide password in row or --default-password)."
            )

        users.append({"username": username, "password": password, "role": role})
    return users


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch create API users from JSON file")
    parser.add_argument("--file", required=True, help="Path to JSON file with users")
    parser.add_argument(
        "--default-role",
        default="coach",
        choices=["admin", "coach", "receptionist"],
        help="Fallback role when row role is omitted",
    )
    parser.add_argument(
        "--default-password",
        default="",
        help="Fallback password when row password is omitted",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate payload and show outcome without inserting rows",
    )
    args = parser.parse_args()

    try:
        raw_items = _load_json(args.file)
        users = _normalize_users(raw_items, args.default_role, args.default_password)
        result = batch_create_api_users({"users": users}, dry_run=args.dry_run)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Input error: {exc}")
        return 2
    except ApiError as exc:
        print(f"API error: {exc}")
        return 1

    print(
        "Batch result:",
        f"total={result.get('total', 0)}",
        f"created={result.get('created', 0)}",
        f"skipped={result.get('skipped', 0)}",
        f"errors={result.get('errors', 0)}",
    )
    for row in result.get("results", []):
        print(
            f"- {row.get('username', '')}: {row.get('status', '')}"
            + (f" ({row.get('detail')})" if row.get("detail") else "")
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
