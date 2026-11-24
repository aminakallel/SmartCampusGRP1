"""Password hashing and compact HS256 JWT handling using Python's stdlib."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.auth.models import UserAccount, UserRole


PASSWORD_HASH_ITERATIONS = 600_000
PASSWORD_SALT_BYTES = 16
JWT_ALGORITHM = "HS256"
JWT_DEFAULT_TTL_SECONDS = 900
JWT_MAX_TTL_SECONDS = 86_400


class InvalidToken(ValueError):
    """Token is malformed, expired, or fails signature/claim validation."""


@dataclass(frozen=True, slots=True)
class JWTSettings:
    secret: bytes
    issuer: str = "smartcampus-api"
    ttl_seconds: int = JWT_DEFAULT_TTL_SECONDS

    @classmethod
    def from_environment(cls) -> "JWTSettings":
        secret = os.environ.get("JWT_SECRET", "").encode("utf-8")
        issuer = os.environ.get("JWT_ISSUER", "smartcampus-api").strip()
        raw_ttl = os.environ.get("JWT_ACCESS_TOKEN_TTL_SECONDS", str(JWT_DEFAULT_TTL_SECONDS))
        try:
            ttl_seconds = int(raw_ttl)
        except ValueError as exc:
            raise RuntimeError("JWT_ACCESS_TOKEN_TTL_SECONDS must be an integer") from exc
        if len(secret) < 32 or secret.lower().startswith(b"replace-with-"):
            raise RuntimeError("JWT_SECRET must contain at least 32 bytes")
        if not issuer:
            raise RuntimeError("JWT_ISSUER must not be empty")
        if not 1 <= ttl_seconds <= JWT_MAX_TTL_SECONDS:
            raise RuntimeError("JWT token lifetime must be between 1 and 86400 seconds")
        return cls(secret=secret, issuer=issuer, ttl_seconds=ttl_seconds)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_HASH_ITERATIONS,
        _b64encode(salt),
        _b64encode(digest),
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, raw_iterations, raw_salt, raw_digest = encoded_hash.split("$", 3)
        iterations = int(raw_iterations)
        salt = _b64decode(raw_salt)
        expected = _b64decode(raw_digest)
        if (
            algorithm != "pbkdf2_sha256"
            or not 100_000 <= iterations <= 1_000_000
            or len(salt) < 16
            or len(expected) != hashlib.sha256().digest_size
        ):
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, iterations
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, UnicodeEncodeError):
        return False


def create_access_token(
    user: UserAccount,
    settings: JWTSettings | None = None,
    now: datetime | None = None,
) -> str:
    config = settings or JWTSettings.from_environment()
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("JWT clock must be timezone-aware")
    issued_at = int(current.timestamp())
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "iss": config.issuer,
        "iat": issued_at,
        "exp": issued_at + config.ttl_seconds,
        "jti": str(uuid4()),
    }
    signing_input = f"{_b64encode(json.dumps(header, separators=(',', ':')).encode())}.{_b64encode(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(config.secret, signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64encode(signature)}"


def decode_access_token(
    token: str,
    settings: JWTSettings | None = None,
    now: datetime | None = None,
) -> dict[str, object]:
    config = settings or JWTSettings.from_environment()
    if not token or len(token) > 8192:
        raise InvalidToken("Invalid bearer token")
    try:
        header_part, payload_part, signature_part = token.split(".")
        header = json.loads(_b64decode(header_part))
        payload = json.loads(_b64decode(payload_part))
        signature = _b64decode(signature_part)
        if not isinstance(header, dict) or header.get("alg") != JWT_ALGORITHM:
            raise InvalidToken("Unsupported JWT algorithm")
        if header.get("typ") != "JWT" or not isinstance(payload, dict):
            raise InvalidToken("Malformed JWT")
        signing_input = f"{header_part}.{payload_part}"
        expected = hmac.new(config.secret, signing_input.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise InvalidToken("Invalid JWT signature")
        if payload.get("iss") != config.issuer:
            raise InvalidToken("Invalid JWT issuer")
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None or current.utcoffset() is None:
            raise ValueError("JWT clock must be timezone-aware")
        now_seconds = int(current.timestamp())
        issued_at = payload.get("iat")
        expires_at = payload.get("exp")
        if not isinstance(issued_at, int) or not isinstance(expires_at, int):
            raise InvalidToken("Missing JWT time claims")
        if issued_at > now_seconds + 30 or expires_at <= now_seconds:
            raise InvalidToken("Expired or not-yet-valid JWT")
        UUID(str(payload.get("sub")))
        if not isinstance(payload.get("email"), str):
            raise InvalidToken("Missing JWT email claim")
        UserRole(payload.get("role"))
        return payload
    except InvalidToken:
        raise
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise InvalidToken("Malformed bearer token") from exc


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    if not value or any(char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for char in value):
        raise ValueError("Invalid base64url value")
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
