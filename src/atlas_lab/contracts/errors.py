class AtlasError(Exception):
    """Base Atlas Lab exception."""


class ValidationError(AtlasError):
    """Raised when an output cannot satisfy the handoff contract."""


class EscalationError(AtlasError):
    """Raised when escalation is required but unavailable."""
