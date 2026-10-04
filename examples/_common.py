"""Shared helpers for the examples. Every example calls `load_config()` first."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

ENV_REMINDER = f"""\
==> REMINDER: add your Freshservice credentials to your ENV file before running examples.

    Create {ENV_FILE} (it is gitignored) containing:

        FRESHSERVICE_DOMAIN=yourcompany.freshservice.com
        FRESHSERVICE_API_KEY=your-api-key

    Find your API key in Freshservice under Profile Settings -> "Your API Key".
"""


def _load_env_file(path: Path) -> None:
    """Minimal KEY=VALUE .env loader; real environment variables take precedence."""
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.removeprefix("export ").strip()
        os.environ.setdefault(key, value.strip().strip("\"'"))


def load_config() -> tuple[str, str]:
    """
    Print the ENV reminder, load .env, and return (domain, api_key).
    Exits with a non-zero status if either value is missing.
    """
    print(ENV_REMINDER)
    _load_env_file(ENV_FILE)

    domain = os.environ.get("FRESHSERVICE_DOMAIN", "")
    api_key = os.environ.get("FRESHSERVICE_API_KEY", "")
    missing = [
        name
        for name, value in (
            ("FRESHSERVICE_DOMAIN", domain),
            ("FRESHSERVICE_API_KEY", api_key),
        )
        if not value
    ]
    if missing:
        sys.exit(f"Missing {', '.join(missing)}. Set it in {ENV_FILE} and run again.")
    return domain, api_key
