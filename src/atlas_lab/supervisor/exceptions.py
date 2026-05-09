from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SupervisorException:
    input_id: str
    reason: str
    requires_human_review: bool = True
