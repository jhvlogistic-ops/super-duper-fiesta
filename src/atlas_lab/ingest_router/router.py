from __future__ import annotations

from atlas_lab.config import AtlasConfig
from atlas_lab.contracts.decisions import RouteDecision
from atlas_lab.contracts.inputs import AtlasInput
from atlas_lab.deterministic_extractors.base import Extractor


class IngestRouter:
    def __init__(self, config: AtlasConfig) -> None:
        self._config = config

    def route(self, item: AtlasInput, extractors: list[Extractor]) -> RouteDecision:
        matching_extractors = [
            extractor.name for extractor in extractors if extractor.can_handle(item)
        ]
        if matching_extractors:
            return RouteDecision(
                input_id=item.id,
                primary_path="deterministic",
                extractors=matching_extractors,
                requires_vision=False,
                reason="deterministic extractor available",
            )

        visual_input = item.source_type in {"image", "dashboard"}
        if visual_input and self._config.enable_vision_escalation:
            return RouteDecision(
                input_id=item.id,
                primary_path="vision",
                extractors=[],
                requires_vision=True,
                reason="visual input requires escalation",
            )

        return RouteDecision(
            input_id=item.id,
            primary_path="reject",
            extractors=[],
            requires_vision=visual_input,
            reason="no extractor available",
        )
