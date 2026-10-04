from __future__ import annotations

from typing import Any

import httpx

from .errors import raise_for_response

# Freshservice ignores the password when authenticating with an API key.
_DUMMY_PASSWORD = "X"


def _build_base_url(endpoint: str) -> str:
    """
    Accepts "acme", "acme.freshservice.com" or "https://acme.freshservice.com"
    (with or without a trailing slash or /api/v2) and returns the API root.
    """
    endpoint = endpoint.strip().rstrip("/")
    if not endpoint:
        raise ValueError("endpoint must not be empty")
    if endpoint.startswith("http://"):
        raise ValueError("Freshservice only supports HTTPS")
    if not endpoint.startswith("https://"):
        if "." not in endpoint:
            endpoint = f"{endpoint}.freshservice.com"
        endpoint = f"https://{endpoint}"
    if not endpoint.endswith("/api/v2"):
        endpoint = f"{endpoint}/api/v2"
    return endpoint


class FreshserviceClient:
    """
    Thin httpx wrapper that authenticates against the Freshservice v2 API.

    https://api.freshservice.com/#authentication
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        *,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ):
        if not api_key:
            raise ValueError("api_key must not be empty")
        self.base_url = _build_base_url(endpoint)
        self._client = httpx.Client(
            base_url=self.base_url,
            auth=httpx.BasicAuth(api_key, _DUMMY_PASSWORD),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=timeout,
            transport=transport,
        )

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Send a request relative to the API root; raises FreshserviceError on failure."""
        response = self._client.request(method, path.lstrip("/"), **kwargs)
        raise_for_response(response)
        return response

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("DELETE", path, **kwargs)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> FreshserviceClient:  # noqa: PYI034 (Self needs py3.11)
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
