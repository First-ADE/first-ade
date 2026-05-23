# implements: FR-021
# traces_to: Π.3.1

"""Custom exception hierarchy for the ADE Compliance Framework.

Provides highly specific, domain-relevant exceptions to improve error handling,
diagnostics, and reporting clarity across CLI, services, and web portals.
"""


class ADEException(Exception):
    """Base exception for all ADE compliance framework errors."""

    pass


class DatabaseException(ADEException):
    """Raised when a database operation, transaction, or migration fails."""

    pass


class ValidationException(ValueError, ADEException):
    """Raised when compliance override parameters or inputs violate validation constraints.

    Inherits from ValueError for complete backward compatibility with standard validators.
    """

    pass


class CryptoAttestationException(ValidationException):
    """Raised specifically when permanent override cryptographic signatures are invalid."""

    pass


class EscalationException(ADEException):
    """Base exception for Human Architect escalation routing failures."""

    pass


class EscalationBlockedException(RuntimeError, EscalationException):
    """Raised when an agent is blocked from execution due to undelivered queue items (fail-closed).

    Inherits from RuntimeError for complete backward compatibility with standard escalators.
    """

    pass
