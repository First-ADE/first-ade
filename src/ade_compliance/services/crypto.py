# implements: FR-021
# traces_to: Π.3.1

"""Cryptographic override signature verification service."""

import base64
from typing import Dict

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

# Memory registry for authorized Human Architects' public keys (loaded at server/cli initialization)
AUTHORIZED_KEYS: Dict[str, rsa.RSAPublicKey] = {}


def register_architect_key(architect_id: str, public_key_pem: bytes) -> None:
    """Register an architect's public key for signature verification."""
    from cryptography.hazmat.primitives import serialization

    key = serialization.load_pem_public_key(public_key_pem)
    if not isinstance(key, rsa.RSAPublicKey):
        raise ValueError("Only RSA public keys are currently supported for override verification.")
    AUTHORIZED_KEYS[architect_id] = key


def verify_sso_signature(architect_id: str, signature_b64: str, rationale: str) -> bool:
    """Verify an architect's signature over a rationale.

    Args:
        architect_id: The SSO ID of the architect (e.g., 'HA-CRYPTO-TEST').
        signature_b64: The base64-encoded signature.
        rationale: The rationale string that was signed.

    Returns:
        bool: True if signature is verified, False otherwise.
    """
    if architect_id not in AUTHORIZED_KEYS:
        return False

    try:
        public_key = AUTHORIZED_KEYS[architect_id]
        signature_bytes = base64.b64decode(signature_b64)

        # Verify RSA PSS signature
        public_key.verify(
            signature_bytes,
            rationale.encode("utf-8"),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False


def decode_and_validate_jwt(token: str, config) -> str:
    """Decode and cryptographically validate an SSO JWT or OIDC token.

    Supports HS256 (symmetric) and RS256 (asymmetric) validation.
    Verifies signature, expiration (exp), and not-before (nbf) claims.

    Args:
        token: The raw JWT/OIDC string.
        config: The framework Config instance.

    Returns:
        str: The authenticated identity (extracted from configured identity_claim).
    """
    import base64
    import hashlib
    import hmac
    import json
    import time

    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    def base64url_decode(s: str) -> bytes:
        s = s.strip()
        rem = len(s) % 4
        if rem > 0:
            s += "=" * (4 - rem)
        return base64.urlsafe_b64decode(s.encode("utf-8"))

    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format: must contain exactly three parts separated by dots.")

    header_b64, payload_b64, signature_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}"

    try:
        header = json.loads(base64url_decode(header_b64).decode("utf-8"))
        payload = json.loads(base64url_decode(payload_b64).decode("utf-8"))
        signature = base64url_decode(signature_b64)
    except Exception as e:
        raise ValueError(f"Failed to decode JWT base64 segments: {e}") from e

    alg = header.get("alg")
    if not alg:
        raise ValueError("JWT header is missing 'alg' parameter.")

    if alg not in config.sso.algorithms:
        raise ValueError(f"JWT algorithm '{alg}' is not permitted by configuration.")

    # 1. Signature Verification
    if alg == "HS256":
        if not config.sso.jwt_secret:
            raise ValueError("JWT configuration error: 'jwt_secret' must be defined to verify HS256 tokens.")
        secret_bytes = config.sso.jwt_secret.encode("utf-8")
        expected_sig = hmac.new(secret_bytes, signing_input.encode("utf-8"), hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected_sig):
            raise ValueError("JWT signature verification failed (HS256).")

    elif alg == "RS256":
        if not config.sso.jwt_public_key:
            raise ValueError("JWT configuration error: 'jwt_public_key' must be defined to verify RS256 tokens.")
        try:
            pub_key = load_pem_public_key(config.sso.jwt_public_key.encode("utf-8"))
            pub_key.verify(signature, signing_input.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
        except Exception as e:
            raise ValueError(f"JWT signature verification failed (RS256): {e}") from e
    else:
        raise ValueError(f"Unsupported signature verification for algorithm '{alg}'.")

    # 2. Claim Validation
    now = int(time.time())
    if "exp" in payload:
        if now >= int(payload["exp"]):
            raise ValueError("JWT has expired (exp claim validation failed).")

    if "nbf" in payload:
        if now < int(payload["nbf"]):
            raise ValueError("JWT is not active yet (nbf claim validation failed).")

    # 3. Identity Extraction
    claim_name = config.sso.identity_claim
    if claim_name not in payload:
        raise ValueError(f"JWT is missing the required identity claim '{claim_name}'.")

    return str(payload[claim_name])
