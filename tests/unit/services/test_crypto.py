# implements: FR-021
# traces_to: Π.2.1

"""Unit tests for the cryptographic signature verification service."""

import base64

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from ade_compliance.services.crypto import (
    AUTHORIZED_KEYS,
    register_architect_key,
    verify_sso_signature,
)


@pytest.fixture(autouse=True)
def clear_keys_registry():
    """Ensure AUTHORIZED_KEYS is cleared before and after each test."""
    AUTHORIZED_KEYS.clear()
    yield
    AUTHORIZED_KEYS.clear()


def test_register_and_verify_valid_signature():
    """Verify that a valid RSA-PSS signature is successfully registered and verified."""
    # 1. Generate an RSA key pair
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # 2. Register key
    architect_id = "HA-TEST-ARCHITECT"
    register_architect_key(architect_id, public_key_pem)

    # 3. Create signature
    rationale = "This is a very long rationale containing cryptographic proof."
    signature = private_key.sign(
        rationale.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    sig_b64 = base64.b64encode(signature).decode("utf-8")

    # 4. Verify signature
    assert verify_sso_signature(architect_id, sig_b64, rationale) is True


def test_verify_unregistered_architect():
    """Verification must fail if the architect key is not registered."""
    rationale = "This is a very long rationale containing cryptographic proof."
    assert verify_sso_signature("HA-UNREGISTERED", "some_sig_b64", rationale) is False


def test_verify_tampered_signature():
    """Verification must fail if the signature or rationale is tampered with."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    architect_id = "HA-TEST-ARCHITECT"
    register_architect_key(architect_id, public_key_pem)

    rationale = "This is a very long rationale containing cryptographic proof."
    signature = private_key.sign(
        rationale.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    sig_b64 = base64.b64encode(signature).decode("utf-8")

    # Tampered signature
    tampered_sig = base64.b64encode(b"completely_different_and_tampered_signature_payload").decode("utf-8")
    assert verify_sso_signature(architect_id, tampered_sig, rationale) is False

    # Tampered rationale
    assert verify_sso_signature(architect_id, sig_b64, rationale + "extra") is False


def test_register_invalid_key_type():
    """Registering a non-RSA public key or invalid PEM bytes must raise ValueError."""
    with pytest.raises(ValueError, match="Only RSA public keys are currently supported"):
        # We pass some arbitrary bytes that serialize to an EC public key or similar,
        # or we just pass something that isn't a valid public key to cause serialization error or type mismatch.
        from cryptography.hazmat.primitives.asymmetric import ec

        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        register_architect_key("HA-EC-TEST", public_key_pem)


def test_register_malformed_key():
    """Registering completely malformed public key bytes must raise ValueError."""
    with pytest.raises(ValueError):
        register_architect_key("HA-MALFORMED", b"not-a-valid-key")
