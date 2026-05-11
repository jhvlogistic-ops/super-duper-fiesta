from __future__ import annotations

from pathlib import Path

from atlas_lab.contracts.inputs import SourceType


def classify_uri(uri: str | None) -> SourceType:
    if uri is None:
        return "unknown"

    suffix = Path(uri).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return "image"
    if suffix == ".pdf":
        return "pdf"
    if suffix in {".csv", ".tsv"}:
        return "table"
    if suffix in {".txt", ".md", ".html"}:
        return "text"
    return "unknown"
