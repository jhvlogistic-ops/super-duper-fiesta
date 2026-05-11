from __future__ import annotations

from atlas_lab.contracts.inputs import AtlasInput, SourceType
from atlas_lab.contracts.observations import EvidenceSpan, ExtractedObservation


class TextParser:
    name = "text_parser"
    supported_types: set[SourceType] = {"text"}

    def can_handle(self, item: AtlasInput) -> bool:
        return item.source_type == "text" and bool(item.raw_text)

    def extract(self, item: AtlasInput) -> ExtractedObservation:
        text = item.raw_text or ""
        return ExtractedObservation(
            input_id=item.id,
            modality="text",
            fields={
                "text": text,
                "char_count": len(text),
                "word_count": len(text.split()),
            },
            evidence=[EvidenceSpan(source=item.uri or item.id, text=text[:500])],
            confidence=0.95 if text else 0.0,
        )
