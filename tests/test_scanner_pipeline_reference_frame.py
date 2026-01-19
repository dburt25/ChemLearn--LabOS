from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from scanner.pipeline import run_pipeline
from scanner.reference_frame import ReferenceFrameUserInputs, ScanRegime


class ScannerPipelineReferenceFrameIntegrationTests(unittest.TestCase):
    def test_pipeline_emits_reference_frame_when_reconstruction_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            run_pipeline(
                output_dir,
                regime=ScanRegime.ROOM_BUILDING,
                points=None,
                user_inputs=ReferenceFrameUserInputs(origin=(1.0, 2.0, 3.0)),
            )

            run_payload = json.loads((output_dir / "run.json").read_text(encoding="utf-8"))
            metrics_payload = json.loads(
                (output_dir / "reconstruction_metrics.json").read_text(encoding="utf-8")
            )

            self.assertIn("reference_frame", run_payload)
            self.assertIn("reference_frame", metrics_payload)
            self.assertEqual(run_payload["reference_frame"]["source"], "user_defined_origin")


if __name__ == "__main__":
    unittest.main()
