from __future__ import annotations

from atlas_lab.contracts.observations import ExtractedObservation
from atlas_lab.contracts.types import JsonValue
from atlas_lab.contracts.validation import SchemaIssue, ValidationResult


class SchemaValidator:
    def __init__(self, min_confidence: float = 0.7) -> None:
        self._min_confidence = min_confidence

    def validate(self, observations: list[ExtractedObservation]) -> ValidationResult:
        issues: list[SchemaIssue] = []
        normalized_fields: dict[str, JsonValue] = {}

        if not observations:
            issues.append(SchemaIssue(code="no_observations", message="No observations found."))
            return ValidationResult(
                valid=False,
                normalized_fields=normalized_fields,
                issues=issues,
                requires_supervisor_review=True,
            )

        for observation in observations:
            if observation.confidence < self._min_confidence:
                issues.append(
                    SchemaIssue(
                        code="low_confidence",
                        message="Observation confidence is below threshold.",
                        field=observation.modality,
                    )
                )
            normalized_fields[observation.modality] = observation.fields

        return ValidationResult(
            valid=not issues,
            normalized_fields=normalized_fields,
            issues=issues,
            requires_supervisor_review=bool(issues),
        )
