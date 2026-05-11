from __future__ import annotations

from atlas_lab.contracts.observations import ExtractedObservation


def average_confidence(observations: list[ExtractedObservation]) -> float:
    if not observations:
        return 0.0
    return sum(observation.confidence for observation in observations) / len(observations)
