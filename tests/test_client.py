import base64

import httpx
import pytest

from freshservice.v2.client import FreshserviceClient, _build_base_url
from freshservice.v2.errors import NotFoundError, RateLimitError, ValidationError


@pytest.mark.parametrize(
    "endpoint",
    [
        "acme",
        "acme.freshservice.com",
        "https://acme.freshservice.com",
        "https://acme.freshservice.com/",
        "https://acme.freshservice.com/api/v2",
    ],
)
def test_build_base_url(endpoint):
    assert _build_base_url(endpoint) == "https://acme.freshservice.com/api/v2"


def test_build_base_url_rejects_http_and_empty():
    with pytest.raises(ValueError):
        _build_base_url("http://acme.freshservice.com")
    with pytest.raises(ValueError):
        _build_base_url("  ")


def test_sends_basic_auth_with_api_key():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["Authorization"]
        return httpx.Response(200, json={"tickets": []})

    with FreshserviceClient(
        "acme", "my-key", transport=httpx.MockTransport(handler)
    ) as client:
        response = client.get("/tickets", params={"page": 2})

    assert response.json() == {"tickets": []}
    assert seen["url"] == "https://acme.freshservice.com/api/v2/tickets?page=2"
    assert seen["auth"] == "Basic " + base64.b64encode(b"my-key:X").decode()


def test_empty_api_key_rejected():
    with pytest.raises(ValueError):
        FreshserviceClient("acme", "")


def test_raises_mapped_errors():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/missing"):
            return httpx.Response(404, json={"description": "Not found"})
        if request.url.path.endswith("/limited"):
            return httpx.Response(429, headers={"Retry-After": "12"})
        return httpx.Response(
            400,
            json={
                "description": "Validation failed",
                "errors": [
                    {"field": "email", "message": "bad", "code": "invalid_value"}
                ],
            },
        )

    with FreshserviceClient(
        "acme", "k", transport=httpx.MockTransport(handler)
    ) as client:
        with pytest.raises(NotFoundError):
            client.get("missing")
        with pytest.raises(RateLimitError) as limited:
            client.get("limited")
        assert limited.value.retry_after == 12
        with pytest.raises(ValidationError) as invalid:
            client.post("tickets", json={})
        assert invalid.value.errors[0].field == "email"
