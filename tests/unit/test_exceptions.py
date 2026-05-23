# implements: FR-021
# traces_to: Π.2.1

"""Unit tests for the custom exception hierarchy in ADE Compliance."""

import pytest

from ade_compliance.exceptions import (
    ADEException,
    CryptoAttestationException,
    DatabaseException,
    EscalationBlockedException,
    EscalationException,
    ValidationException,
)


def test_exception_inheritance():
    """Verify that custom exceptions inherit correctly from ADEException and standard bases."""
    # Base Exception
    assert issubclass(ADEException, Exception)

    # Database Exception
    assert issubclass(DatabaseException, ADEException)

    # Validation Exceptions
    assert issubclass(ValidationException, ADEException)
    assert issubclass(ValidationException, ValueError)  # Backward compatibility check

    # Crypto Attestation Exception
    assert issubclass(CryptoAttestationException, ValidationException)
    assert issubclass(CryptoAttestationException, ValueError)

    # Escalation Exceptions
    assert issubclass(EscalationException, ADEException)
    assert issubclass(EscalationBlockedException, EscalationException)
    assert issubclass(EscalationBlockedException, RuntimeError)  # Backward compatibility check


def test_validation_exception_raising():
    """Verify ValidationException behaves as a ValueError."""
    with pytest.raises(ValidationException):
        raise ValidationException("Invalid validation parameters.")

    with pytest.raises(ValueError):
        raise ValidationException("Must behave as a ValueError.")


def test_crypto_attestation_exception_raising():
    """Verify CryptoAttestationException behaves as a ValueError."""
    with pytest.raises(CryptoAttestationException):
        raise CryptoAttestationException("Invalid signature.")

    with pytest.raises(ValueError):
        raise CryptoAttestationException("Must behave as a ValueError.")


def test_escalation_blocked_exception_raising():
    """Verify EscalationBlockedException behaves as a RuntimeError."""
    with pytest.raises(EscalationBlockedException):
        raise EscalationBlockedException("Agent is blocked.")

    with pytest.raises(RuntimeError):
        raise EscalationBlockedException("Must behave as a RuntimeError.")
