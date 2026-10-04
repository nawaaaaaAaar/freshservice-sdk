from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any


class StatusCodes(IntEnum):
    """
    As defined here: https://api.freshservice.com/#error
    """

    ClientOrValidationError = 400
    AuthenticationFailure = 401
    AccessDenied = 403
    NotFound = 404
    NotAllowed = 405
    UnsupportedHeader = 406
    InconsistentState = 409
    UnsupportedContentType = 415
    RateLimitExceeded = 429
    ServerError = 500


class ErrorCode(str, Enum):
    """
    Machine parseable error codes: https://api.freshservice.com/#error
    """

    MissingField = "missing_field"
    InvalidValue = "invalid_value"
    DuplicateValue = "duplicate_value"
    DatatypeMismatch = "datatype_mismatch"
    InvalidField = "invalid_field"
    InvalidJson = "invalid_json"
    InvalidCredentials = "invalid_credentials"
    AccessDenied = "access_denied"
    RequireFeature = "require_feature"
    AccountSuspended = "account_suspended"
    SslRequired = "ssl_required"
    ReadonlyField = "readonly_field"
    PasswordLockout = "password_lockout"
    PasswordExpired = "password_expired"
    InaccessibleField = "inaccessible_field"
    IncompatibleField = "incompatible_field"
    UnsupportedAuthenticationType = "unsupported_authentication_type"
    AccessTokenExpired = "access_token_expired"
    AccessTokenInvalid = "access_token_invalid"
    Unknown = "unknown"

    @classmethod
    def _missing_(cls, value: object) -> ErrorCode:
        # The API may add codes over time; don't crash on ones we don't know.
        return cls.Unknown


@dataclass(frozen=True)
class ErrorResponse:
    message: str
    code: ErrorCode
    field: str | None = None  # only present on 400 responses

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ErrorResponse:
        return cls(
            message=data.get("message", ""),
            code=ErrorCode(data.get("code", "unknown")),
            field=data.get("field"),
        )


class FreshserviceError(Exception):
    status_code: int | None = None

    def __init__(
        self,
        description: str = "",
        errors: list[ErrorResponse] | None = None,
        status_code: int | None = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(description)
        self.description = description
        self.errors = errors or []
        self.headers = headers or {}
        if status_code is not None:
            self.status_code = status_code

    def __str__(self) -> str:
        details = "; ".join(
            f"{e.field + ': ' if e.field else ''}{e.message} ({e.code.value})"
            for e in self.errors
        )
        return f"[{self.status_code}] {self.description}" + (
            f" - {details}" if details else ""
        )


class ValidationError(FreshserviceError):
    status_code = StatusCodes.ClientOrValidationError


class AuthenticationError(FreshserviceError):
    status_code = StatusCodes.AuthenticationFailure


class AccessDeniedError(FreshserviceError):
    status_code = StatusCodes.AccessDenied


class NotFoundError(FreshserviceError):
    status_code = StatusCodes.NotFound


class MethodNotAllowedError(FreshserviceError):
    status_code = StatusCodes.NotAllowed


class UnsupportedHeaderError(FreshserviceError):
    status_code = StatusCodes.UnsupportedHeader


class ConflictError(FreshserviceError):
    status_code = StatusCodes.InconsistentState


class UnsupportedContentTypeError(FreshserviceError):
    status_code = StatusCodes.UnsupportedContentType


class ServerError(FreshserviceError):
    status_code = StatusCodes.ServerError


class RateLimitError(FreshserviceError):
    status_code = StatusCodes.RateLimitExceeded

    @property
    def retry_after(self) -> int | None:
        """Seconds to wait before retrying, from the Retry-After header."""
        value = next(
            (v for k, v in self.headers.items() if k.lower() == "retry-after"), None
        )
        return int(value) if value and value.isdigit() else None


_EXCEPTIONS: dict[int, type[FreshserviceError]] = {
    cls.status_code: cls
    for cls in (
        ValidationError,
        AuthenticationError,
        AccessDeniedError,
        NotFoundError,
        MethodNotAllowedError,
        UnsupportedHeaderError,
        ConflictError,
        UnsupportedContentTypeError,
        RateLimitError,
        ServerError,
    )
}


def raise_for_response(response) -> None:
    """Raise the matching FreshserviceError for a failed `httpx.Response`."""
    if response.is_success:
        return
    try:
        body = response.json()
    except ValueError:
        body = {}
    errors = [ErrorResponse.from_dict(e) for e in body.get("errors", [])]
    cls = _EXCEPTIONS.get(response.status_code, FreshserviceError)
    raise cls(
        body.get("description", response.reason_phrase or ""),
        errors,
        response.status_code,
        dict(response.headers),
    )
