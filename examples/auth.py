"""
Authenticate to the Freshservice API and print your API key.

Run from the repo root:

    uv run python examples/auth.py
"""

from __future__ import annotations

from _common import load_config

from freshservice.v2.client import FreshserviceClient
from freshservice.v2.errors import FreshserviceError


def main() -> None:
    domain, api_key = load_config()

    try:
        with FreshserviceClient(domain, api_key) as client:
            # /agents/me returns the agent that owns the API key, so a 200
            # proves the key is valid.
            agent = client.get("agents/me").json()["agent"]
    except FreshserviceError as exc:
        raise SystemExit(f"Authentication failed: {exc}") from exc

    print(
        f"Authenticated as {agent['first_name']} {agent['last_name']} ({agent['email']})"
    )
    print(f"API key: {api_key}")


if __name__ == "__main__":
    main()
