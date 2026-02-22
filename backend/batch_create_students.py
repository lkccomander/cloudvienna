import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api_client import ApiError, batch_create_students


def _load_students(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        data = data.get("students", [])
    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list or an object with key 'students'.")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch create students from JSON file")
    parser.add_argument("--file", required=True, help="Path to JSON file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate payload and show outcome without inserting rows",
    )
    args = parser.parse_args()

    try:
        students = _load_students(args.file)
        result = batch_create_students({"students": students}, dry_run=args.dry_run)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Input error: {exc}")
        return 2
    except ApiError as exc:
        print(f"API error: {exc}")
        return 1

    print(
        "Batch result:",
        f"total={result.get('total', 0)}",
        f"created={result.get('created', 0)}",
        f"errors={result.get('errors', 0)}",
    )
    for row in result.get("results", []):
        print(
            f"- {row.get('name', '')} <{row.get('email', '')}>: {row.get('status', '')}"
            + (f" ({row.get('detail')})" if row.get("detail") else "")
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
