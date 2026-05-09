from __future__ import annotations

from atlas_lab.contracts.handoff import HandoffPackage
from atlas_lab.contracts.inputs import AtlasInput
from atlas_lab.contracts.observations import ExtractedObservation
from atlas_lab.contracts.validation import ValidationResult
from atlas_lab.schema_validator.confidence import average_confidence


class HandoffWriter:
    def build(
        self,
        item: AtlasInput,
        validation: ValidationResult,
        observations: list[ExtractedObservation],
    ) -> HandoffPackage:
        target = "quantlabx" if validation.valid else "supervisor"
        return HandoffPackage(
            id=f"handoff-{item.id}",
            target=target,
            source_input_id=item.id,
            observations=observations,
            validated_payload=validation.normalized_fields,
            confidence=average_confidence(observations),
            audit_trace=[
                "atlas_lab.ingest_router",
                "atlas_lab.deterministic_extractors",
                "atlas_lab.schema_validator",
                "atlas_lab.handoff_writer",
            ],
            permissions={
                "can_execute_trades": False,
                "can_decide_risk": False,
                "can_override_quantlabx": False,
            },
        )
