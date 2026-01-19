from pathlib import Path
import sys
import unittest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from scanner.reference_frame import (
    ReferenceFramePolicy,
    ReferenceFrameSource,
    ReferenceFrameUserInputs,
    ScanRegime,
    compute_bbox_center,
    resolve_reference_frame,
    translate_points,
)


class ReferenceFrameUnitTests(unittest.TestCase):
    def test_bbox_center_computation(self):
        points = [(0.0, 0.0, 0.0), (2.0, 2.0, 2.0)]
        self.assertEqual(compute_bbox_center(points), (1.0, 1.0, 1.0))

    def test_translation_correctness(self):
        points = [(1.0, 2.0, 3.0), (4.0, 5.0, 6.0)]
        origin = (1.0, 1.0, 1.0)
        self.assertEqual(translate_points(points, origin), [(0.0, 1.0, 2.0), (3.0, 4.0, 5.0)])

    def test_small_object_requires_explicit_origin(self):
        policy = ReferenceFramePolicy.for_regime(ScanRegime.SMALL_OBJECT)
        with self.assertRaises(ValueError):
            resolve_reference_frame(
                points=[(0.0, 0.0, 0.0)],
                policy=policy,
                user_inputs=ReferenceFrameUserInputs(),
            )

    def test_room_building_allows_heuristic_center(self):
        policy = ReferenceFramePolicy.for_regime(ScanRegime.ROOM_BUILDING)
        result = resolve_reference_frame(
            points=[(0.0, 0.0, 0.0), (2.0, 2.0, 2.0)],
            policy=policy,
            user_inputs=ReferenceFrameUserInputs(),
        )
        self.assertEqual(result.source, ReferenceFrameSource.BBOX_CENTER)
        self.assertEqual(result.origin_xyz, (1.0, 1.0, 1.0))


if __name__ == "__main__":
    unittest.main()
