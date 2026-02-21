import json
import os
import urllib.error
import urllib.request

import pytest


def test_api_health_endpoint():
    base_url = (os.getenv("API_BASE_URL") or "http://127.0.0.1:8000").rstrip("/")
    url = f"{base_url}/health"

    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body) if body else {}
            assert response.status == 200
            assert data.get("status") == "ok"
    except urllib.error.URLError as exc:
        pytest.fail(f"API health check failed for {url}: {exc.reason}")

    print("-✅")
