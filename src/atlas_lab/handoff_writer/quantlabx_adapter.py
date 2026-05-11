from __future__ import annotations

from atlas_lab.contracts.handoff import HandoffPackage
from atlas_lab.contracts.types import JsonValue


def to_quantlabx_payload(package: HandoffPackage) -> dict[str, JsonValue]:
    return {
        "source_input_id": package.source_input_id,
        "payload": package.validated_payload,
        "confidence": package.confidence,
        "audit_trace": package.audit_trace,
        "permissions": package.permissions,
    }
