from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RoutePath = Literal["deterministic", "vision", "reject"]


@dataclass(frozen=True, slots=True)
class RouteDecision:
    input_id: str
    primary_path: RoutePath
    extractors: list[str]
    requires_vision: bool
    reason: str
