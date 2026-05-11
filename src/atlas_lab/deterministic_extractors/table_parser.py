from __future__ import annotations

import csv
from io import StringIO

from atlas_lab.contracts.inputs import AtlasInput, SourceType
from atlas_lab.contracts.observations import EvidenceSpan, ExtractedObservation


class TableParser:
    name = "table_parser"
    supported_types: set[SourceType] = {"table"}

    def can_handle(self, item: AtlasInput) -> bool:
        return item.source_type == "table" and bool(item.raw_text)

    def extract(self, item: AtlasInput) -> ExtractedObservation:
        text = item.raw_text or ""
        rows = list(csv.DictReader(StringIO(text)))
        columns = list(rows[0].keys()) if rows else []
        return ExtractedObservation(
            input_id=item.id,
            modality="table",
            fields={
                "columns": columns,
                "row_count": len(rows),
                "rows": rows,
            },
            evidence=[EvidenceSpan(source=item.uri or item.id, text=text[:500])],
            confidence=0.9 if rows else 0.4,
            warnings=[] if rows else ["empty or header-only table"],
        )
