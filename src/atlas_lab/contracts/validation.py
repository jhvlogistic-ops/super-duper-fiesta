from __future__ import annotations

from dataclasses import dataclass, field

from atlas_lab.contracts.types import JsonValue


@dataclass(frozen=True, slots=True)
class SchemaIssue:
    code: str
    message: str
    field: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: bool
    normalized_fields: dict[str, JsonValue]
    issues: list[SchemaIssue] = field(default_factory=list)
    requires_supervisor_review: bool = False
