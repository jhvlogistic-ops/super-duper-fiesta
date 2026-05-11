from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from atlas_lab.contracts.types import JsonValue

SourceType = Literal["image", "pdf", "table", "text", "dashboard", "unknown"]


@dataclass(frozen=True, slots=True)
class SourceMetadata:
    source_name: str | None = None
    created_at: str | None = None
    tags: tuple[str, ...] = ()
    attributes: dict[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AtlasInput:
    id: str
    source_type: SourceType
    uri: str | None = None
    raw_text: str | None = None
    metadata: SourceMetadata = field(default_factory=SourceMetadata)
