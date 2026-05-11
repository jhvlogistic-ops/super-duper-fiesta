from __future__ import annotations

from atlas_lab.contracts.errors import EscalationError
from atlas_lab.contracts.inputs import AtlasInput
from atlas_lab.contracts.observations import ExtractedObservation


class StubVisionReasoner:
    name = "stub_vision_reasoner"

    def reason(
        self,
        item: AtlasInput,
        context: list[ExtractedObservation],
    ) -> ExtractedObservation:
        raise EscalationError("Vision reasoning is intentionally stubbed in MVP.")
