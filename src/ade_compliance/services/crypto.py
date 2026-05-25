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
    import jwt
    from jwt.exceptions import (
        DecodeError,
        ExpiredSignatureError,
        ImmatureSignatureError,
        InvalidSignatureError,
        InvalidTokenError,
    )

    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format: must contain exactly three parts separated by dots.")

        try:
            header = jwt.get_unverified_header(token)
        except Exception as e:
            raise ValueError(f"Failed to decode JWT base64 segments: {e}") from e

        alg = header.get("alg")
        if not alg:
            raise ValueError("JWT header is missing 'alg' parameter.")

        if alg not in config.sso.algorithms:
            raise ValueError(f"JWT algorithm '{alg}' is not permitted by configuration.")

        if alg == "HS256":
            if not config.sso.jwt_secret:
                raise ValueError("JWT configuration error: 'jwt_secret' must be defined to verify HS256 tokens.")
            key = config.sso.jwt_secret
        elif alg == "RS256":
            if not config.sso.jwt_public_key:
                raise ValueError("JWT configuration error: 'jwt_public_key' must be defined to verify RS256 tokens.")
            key = config.sso.jwt_public_key
        else:
            raise ValueError(f"Unsupported signature verification for algorithm '{alg}'.")

        import warnings

        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=jwt.InsecureKeyLengthWarning)
                payload = jwt.decode(token, key, algorithms=[alg])
        except ExpiredSignatureError as e:
            raise ValueError("JWT has expired (exp claim validation failed).") from e
        except ImmatureSignatureError as e:
            raise ValueError("JWT is not active yet (nbf claim validation failed).") from e
        except (InvalidSignatureError, DecodeError) as e:
            if alg == "HS256":
                raise ValueError("JWT signature verification failed (HS256).") from e
            else:
                raise ValueError(f"JWT signature verification failed (RS256): {e}") from e
        except InvalidTokenError as e:
            raise ValueError(f"JWT verification failed: {e}") from e

        claim_name = config.sso.identity_claim
        if claim_name not in payload:
            raise ValueError(f"JWT is missing the required identity claim '{claim_name}'.")

        return str(payload[claim_name])

    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(str(e)) from e
