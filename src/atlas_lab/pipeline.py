from __future__ import annotations

from atlas_lab.config import AtlasConfig
from atlas_lab.contracts.handoff import HandoffPackage
from atlas_lab.contracts.inputs import AtlasInput
from atlas_lab.deterministic_extractors.base import Extractor
from atlas_lab.deterministic_extractors.table_parser import TableParser
from atlas_lab.deterministic_extractors.text_parser import TextParser
from atlas_lab.handoff_writer.writer import HandoffWriter
from atlas_lab.ingest_router.router import IngestRouter
from atlas_lab.schema_validator.validator import SchemaValidator


def default_extractors() -> list[Extractor]:
    return [TextParser(), TableParser()]


def run_pipeline(
    item: AtlasInput,
    config: AtlasConfig | None = None,
    extractors: list[Extractor] | None = None,
) -> HandoffPackage:
    runtime_config = config or AtlasConfig()
    router = IngestRouter(config=runtime_config)
    selected_extractors = extractors or default_extractors()
    route = router.route(item, selected_extractors)

    observations = [
        extractor.extract(item)
        for extractor in selected_extractors
        if extractor.name in route.extractors
    ]

    validation = SchemaValidator(min_confidence=runtime_config.min_confidence).validate(
        observations
    )
    return HandoffWriter().build(item, validation, observations)
