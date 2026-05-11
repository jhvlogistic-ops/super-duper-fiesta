# Atlas Lab

Atlas Lab is a frugal, auditable, event-driven multimodal utility layer
subordinated to QuantLabX.

QuantLabX keeps authority over deterministic execution, risk, backtests, and
metrics. Atlas Lab only observes, extracts, validates, and writes structured
handoff payloads.

## MVP modules

- `ingest_router`: chooses deterministic extraction, visual escalation, or reject.
- `deterministic_extractors`: parses structured text/table inputs first.
- `vision_reasoner`: optional exceptional escalation boundary, stubbed in MVP.
- `schema_validator`: validates confidence and normalized payloads.
- `handoff_writer`: produces auditable non-execution handoff packages.
- `supervisor`: supports review-by-exception primitives.

## Boundary rule

Atlas Lab does not execute trades, decide risk, override governance, or replace
QuantLabX deterministic validation.

## Local validation

```bash
PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests
```
