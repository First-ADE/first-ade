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


def test_exception_raising():
    """Verify raising custom exceptions behaves exactly as expected."""
    # 1. ValidationException
    try:
        raise ValidationException("Invalid validation parameters.")
    except ValidationException:
        pass
    else:
        pytest.fail("ValidationException not raised")

    try:
        raise ValidationException("Must behave as a ValueError.")
    except ValueError:
        pass
    else:
        pytest.fail("ValidationException not caught as ValueError")

    # 2. CryptoAttestationException
    try:
        raise CryptoAttestationException("Invalid signature.")
    except CryptoAttestationException:
        pass
    else:
        pytest.fail("CryptoAttestationException not raised")

    try:
        raise CryptoAttestationException("Must behave as a ValueError.")
    except ValueError:
        pass
    else:
        pytest.fail("CryptoAttestationException not caught as ValueError")

    # 3. EscalationBlockedException
    try:
        raise EscalationBlockedException("Agent is blocked.")
    except EscalationBlockedException:
        pass
    else:
        pytest.fail("EscalationBlockedException not raised")

    try:
        raise EscalationBlockedException("Must behave as a RuntimeError.")
    except RuntimeError:
        pass
    else:
        pytest.fail("EscalationBlockedException not caught as RuntimeError")
