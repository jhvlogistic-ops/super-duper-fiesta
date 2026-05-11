from __future__ import annotations

from atlas_lab.contracts.errors import EscalationError
from atlas_lab.contracts.inputs import AtlasInput, SourceType
from atlas_lab.contracts.observations import ExtractedObservation


class OcrParser:
    name = "ocr_parser"
    supported_types: set[SourceType] = {"image", "dashboard"}

    def can_handle(self, item: AtlasInput) -> bool:
        return item.source_type in self.supported_types

    def extract(self, item: AtlasInput) -> ExtractedObservation:
        raise EscalationError("OCR adapter is intentionally stubbed in the MVP skeleton.")
