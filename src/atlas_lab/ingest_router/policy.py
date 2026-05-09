from __future__ import annotations

from atlas_lab.contracts.validation import ValidationResult


def should_escalate_to_vision(validation: ValidationResult) -> bool:
    return not validation.valid or validation.requires_supervisor_review
