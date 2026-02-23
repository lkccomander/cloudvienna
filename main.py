"""Compatibility API entrypoint.

Canonical API implementation lives in backend.main.
This module is kept so existing commands like `python main.py` keep working.
"""

from backend.main import app  # Re-export for ASGI servers
from backend.run import main as run_backend


if __name__ == "__main__":
    run_backend()
