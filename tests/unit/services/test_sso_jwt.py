# implements: FR-021
# traces_to: Π.2.1

import base64
import hashlib
import hmac
import json
import time

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from fastapi import HTTPException

from ade_compliance.config import Config
from ade_compliance.server import get_current_sso_user
from ade_compliance.services.crypto import decode_and_validate_jwt


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def create_test_jwt(payload: dict, secret_or_key, alg: str = "HS256") -> str:
    header = {"alg": alg, "typ": "JWT"}
    header_b64 = base64url_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = base64url_encode(json.dumps(payload).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}"

    if alg == "HS256":
        secret_bytes = secret_or_key.encode("utf-8")
        signature = hmac.new(secret_bytes, signing_input.encode("utf-8"), hashlib.sha256).digest()
    elif alg == "RS256":
        signature = secret_or_key.sign(signing_input.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
    else:
        raise ValueError("Unsupported algorithm")

    sig_b64 = base64url_encode(signature)
    return f"{signing_input}.{sig_b64}"


def test_hs256_jwt_validation_success():
    """Verify that a valid HS256 JWT is successfully validated and the claim is extracted."""
    config = Config()
    config.sso.enabled = True
    config.sso.jwt_secret = "super-secret-key-12345"
    config.sso.identity_claim = "sub"

    payload = {"sub": "architect-john", "exp": int(time.time()) + 3600, "nbf": int(time.time()) - 60}
    token = create_test_jwt(payload, config.sso.jwt_secret, alg="HS256")

    user = decode_and_validate_jwt(token, config)
    assert user == "architect-john"


def test_rs256_jwt_validation_success():
    """Verify that a valid RS256 JWT is successfully validated via public key."""
    config = Config()
    config.sso.enabled = True
    config.sso.identity_claim = "email"

    # Generate RSA key pair
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )

    config.sso.jwt_public_key = public_key_pem

    payload = {"email": "architect-jane@first-ade.org", "exp": int(time.time()) + 3600}
    token = create_test_jwt(payload, private_key, alg="RS256")

    user = decode_and_validate_jwt(token, config)
    assert user == "architect-jane@first-ade.org"


def test_expired_jwt_rejected():
    """Verify that an expired JWT is rejected with a ValueError."""
    config = Config()
    config.sso.enabled = True
    config.sso.jwt_secret = "secret"

    payload = {
        "sub": "architect-john",
        "exp": int(time.time()) - 10,  # Expired
    }
    token = create_test_jwt(payload, config.sso.jwt_secret, alg="HS256")

    with pytest.raises(ValueError, match="JWT has expired"):
        decode_and_validate_jwt(token, config)


def test_nbf_not_active_jwt_rejected():
    """Verify that a JWT before its 'nbf' time is rejected with a ValueError."""
    config = Config()
    config.sso.enabled = True
    config.sso.jwt_secret = "secret"

    payload = {
        "sub": "architect-john",
        "nbf": int(time.time()) + 3600,  # Not active for 1 hour
    }
    token = create_test_jwt(payload, config.sso.jwt_secret, alg="HS256")

    with pytest.raises(ValueError, match="JWT is not active yet"):
        decode_and_validate_jwt(token, config)


def test_invalid_signature_rejected():
    """Verify that a tampered signature is rejected."""
    config = Config()
    config.sso.enabled = True
    config.sso.jwt_secret = "secret"

    payload = {
        "sub": "architect-john",
    }
    token = create_test_jwt(payload, config.sso.jwt_secret, alg="HS256")
    parts = token.split(".")

    # Tamper with signature part
    tampered_token = f"{parts[0]}.{parts[1]}.{parts[2]}extra"

    with pytest.raises(ValueError, match="JWT signature verification failed"):
        decode_and_validate_jwt(tampered_token, config)


class MockApp:
    def __init__(self, config):
        self.state = type("State", (), {"config": config})()


class MockRequest:
    def __init__(self, config):
        self.app = MockApp(config)


@pytest.mark.asyncio
async def test_server_jwt_sso_integration():
    """Verify get_current_sso_user routing with JWT SSO enabled and legacy fallback."""
    # 1. JWT SSO Enabled
    config = Config()
    config.sso.enabled = True
    config.sso.jwt_secret = "secret"

    request = MockRequest(config)
    payload = {"sub": "jwt-architect"}
    token = create_test_jwt(payload, config.sso.jwt_secret, alg="HS256")

    # Happy path
    user = get_current_sso_user(request, authorization=f"Bearer {token}")
    assert user == "jwt-architect"

    # Missing Authorization Header
    with pytest.raises(HTTPException) as exc_info:
        get_current_sso_user(request, authorization=None)
    assert exc_info.value.status_code == 401
    assert "Missing Authorization" in exc_info.value.detail

    # 2. JWT SSO Disabled (Legacy Fallback)
    config_disabled = Config()
    config_disabled.sso.enabled = False
    request_disabled = MockRequest(config_disabled)

    # Happy legacy path
    user_legacy = get_current_sso_user(request_disabled, x_sso_user="legacy-architect")
    assert user_legacy == "legacy-architect"

    # Missing legacy header
    with pytest.raises(HTTPException) as exc_info:
        get_current_sso_user(request_disabled, x_sso_user=None)
    assert exc_info.value.status_code == 401
    assert "Missing X-SSO-User" in exc_info.value.detail
