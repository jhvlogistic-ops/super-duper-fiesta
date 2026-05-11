from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AtlasConfig:
    min_confidence: float = 0.7
    enable_vision_escalation: bool = False
