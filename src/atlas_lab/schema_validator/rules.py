from __future__ import annotations

from atlas_lab.contracts.handoff import HandoffPackage


def enforces_non_execution_boundary(package: HandoffPackage) -> bool:
    return not package.permissions.get("can_execute_trades", False)
