from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from atlas_lab.contracts.observations import ExtractedObservation
from atlas_lab.contracts.types import JsonValue

HandoffTarget = Literal["quantlabx", "supervisor"]


@dataclass(frozen=True, slots=True)
class HandoffPackage:
    id: str
    target: HandoffTarget
    source_input_id: str
    observations: list[ExtractedObservation]
    validated_payload: dict[str, JsonValue]
    confidence: float
    audit_trace: list[str] = field(default_factory=list)
    permissions: dict[str, bool] = field(default_factory=dict)
