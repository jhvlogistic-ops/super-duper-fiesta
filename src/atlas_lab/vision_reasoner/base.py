from __future__ import annotations

from typing import Protocol

from atlas_lab.contracts.inputs import AtlasInput
from atlas_lab.contracts.observations import ExtractedObservation


class VisionReasoner(Protocol):
    name: str

    def reason(
        self,
        item: AtlasInput,
        context: list[ExtractedObservation],
    ) -> ExtractedObservation: ...
