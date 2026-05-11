from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from atlas_lab.contracts.types import JsonValue

ObservationModality = Literal["ocr", "pdf", "table", "text", "vision"]


@dataclass(frozen=True, slots=True)
class EvidenceSpan:
    source: str
    text: str
    start: int | None = None
    end: int | None = None


@dataclass(frozen=True, slots=True)
class ExtractedObservation:
    input_id: str
    modality: ObservationModality
    fields: dict[str, JsonValue]
    evidence: list[EvidenceSpan] = field(default_factory=list)
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)
