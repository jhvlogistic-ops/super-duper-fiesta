from __future__ import annotations

import unittest

from atlas_lab.contracts.inputs import AtlasInput
from atlas_lab.pipeline import run_pipeline


class PipelineTest(unittest.TestCase):
    def test_text_input_handoffs_to_quantlabx(self) -> None:
        package = run_pipeline(
            AtlasInput(
                id="sample-text",
                source_type="text",
                raw_text="Atlas observes; QuantLabX decides.",
            )
        )

        self.assertEqual(package.target, "quantlabx")
        self.assertFalse(package.permissions["can_execute_trades"])
        self.assertEqual(package.validated_payload["text"]["word_count"], 4)

    def test_unknown_input_handoffs_to_supervisor(self) -> None:
        package = run_pipeline(AtlasInput(id="unknown", source_type="unknown"))

        self.assertEqual(package.target, "supervisor")
        self.assertFalse(package.permissions["can_decide_risk"])
        self.assertEqual(package.validated_payload, {})


if __name__ == "__main__":
    unittest.main()
