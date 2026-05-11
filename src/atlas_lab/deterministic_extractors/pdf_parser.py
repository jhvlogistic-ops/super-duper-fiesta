from __future__ import annotations

from atlas_lab.contracts.errors import EscalationError
from atlas_lab.contracts.inputs import AtlasInput, SourceType
from atlas_lab.contracts.observations import ExtractedObservation


class PdfParser:
    name = "pdf_parser"
    supported_types: set[SourceType] = {"pdf"}

    def can_handle(self, item: AtlasInput) -> bool:
        return item.source_type == "pdf"

    def extract(self, item: AtlasInput) -> ExtractedObservation:
        raise EscalationError("PDF adapter is intentionally stubbed in the MVP skeleton.")
