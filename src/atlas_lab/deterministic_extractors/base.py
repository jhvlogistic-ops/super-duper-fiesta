from __future__ import annotations

from typing import Protocol

from atlas_lab.contracts.inputs import AtlasInput, SourceType
from atlas_lab.contracts.observations import ExtractedObservation


class Extractor(Protocol):
    name: str
    supported_types: set[SourceType]

    def can_handle(self, item: AtlasInput) -> bool: ...

    def extract(self, item: AtlasInput) -> ExtractedObservation: ...
