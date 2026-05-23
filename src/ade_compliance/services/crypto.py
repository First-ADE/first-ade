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
