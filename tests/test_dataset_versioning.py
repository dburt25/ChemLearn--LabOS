"""Tests for dataset versioning system."""

import unittest
from datetime import datetime

from labos.core.datasets import DatasetRef


class TestDatasetVersioning(unittest.TestCase):
    """Test dataset semantic versioning and evolution tracking."""

    def test_default_version_is_1_0_0(self):
        """New datasets default to version 1.0.0."""
        ds = DatasetRef(id="DS-001", label="Test")
        self.assertEqual(ds.version, "1.0.0")

    def test_parent_version_defaults_to_none(self):
        """New datasets have no parent version."""
        ds = DatasetRef(id="DS-002", label="Test")
        self.assertIsNone(ds.parent_version)

    def test_bump_major_increments_major_version(self):
        """bump_major() increments major version and resets minor/patch."""
        ds = DatasetRef(id="DS-003", label="Test", version="1.2.3")
        ds_v2 = ds.bump_major()
        self.assertEqual(ds_v2.version, "2.0.0")
        self.assertEqual(ds_v2.parent_version, "1.2.3")

    def test_bump_minor_increments_minor_version(self):
        """bump_minor() increments minor version and resets patch."""
        ds = DatasetRef(id="DS-004", label="Test", version="1.2.3")
        ds_v2 = ds.bump_minor()
        self.assertEqual(ds_v2.version, "1.3.0")
        self.assertEqual(ds_v2.parent_version, "1.2.3")

    def test_bump_patch_increments_patch_version(self):
        """bump_patch() increments patch version only."""
        ds = DatasetRef(id="DS-005", label="Test", version="1.2.3")
        ds_v2 = ds.bump_patch()
        self.assertEqual(ds_v2.version, "1.2.4")
        self.assertEqual(ds_v2.parent_version, "1.2.3")

    def test_bumped_version_preserves_id_and_label(self):
        """Version bumps preserve id and label."""
        ds = DatasetRef(id="DS-006", label="Original", version="1.0.0")
        ds_v2 = ds.bump_minor()
        self.assertEqual(ds_v2.id, "DS-006")
        self.assertEqual(ds_v2.label, "Original")

    def test_bumped_version_preserves_kind(self):
        """Version bumps preserve dataset kind."""
        ds = DatasetRef(id="DS-007", label="Test", kind="spectrum", version="1.0.0")
        ds_v2 = ds.bump_patch()
        self.assertEqual(ds_v2.kind, "spectrum")

    def test_bumped_version_preserves_metadata(self):
        """Version bumps preserve metadata."""
        ds = DatasetRef(id="DS-008", label="Test", metadata={"key": "value"}, version="1.0.0")
        ds_v2 = ds.bump_major()
        self.assertEqual(ds_v2.metadata, {"key": "value"})

    def test_bumped_version_has_new_created_at(self):
        """Version bumps get new created_at timestamp."""
        ds = DatasetRef(id="DS-009", label="Test", version="1.0.0")
        old_created_at = ds.created_at
        import time
        time.sleep(0.001)
        ds_v2 = ds.bump_patch()
        self.assertGreater(ds_v2.created_at, old_created_at)

    def test_version_chain_tracking(self):
        """Can track version evolution chain."""
        ds_v1 = DatasetRef(id="DS-010", label="Test", version="1.0.0")
        self.assertIsNone(ds_v1.parent_version)
        
        ds_v2 = ds_v1.bump_minor()
        self.assertEqual(ds_v2.version, "1.1.0")
        self.assertEqual(ds_v2.parent_version, "1.0.0")
        
        ds_v3 = ds_v2.bump_patch()
        self.assertEqual(ds_v3.version, "1.1.1")
        self.assertEqual(ds_v3.parent_version, "1.1.0")
        
        ds_v4 = ds_v3.bump_major()
        self.assertEqual(ds_v4.version, "2.0.0")
        self.assertEqual(ds_v4.parent_version, "1.1.1")

    def test_get_version_tuple(self):
        """get_version_tuple() returns (major, minor, patch)."""
        ds = DatasetRef(id="DS-011", label="Test", version="2.5.7")
        self.assertEqual(ds.get_version_tuple(), (2, 5, 7))

    def test_version_tuple_for_comparison(self):
        """Version tuples can be compared for ordering."""
        ds1 = DatasetRef(id="DS-012", label="Test", version="1.2.3")
        ds2 = DatasetRef(id="DS-012", label="Test", version="1.2.4")
        ds3 = DatasetRef(id="DS-012", label="Test", version="2.0.0")
        
        self.assertLess(ds1.get_version_tuple(), ds2.get_version_tuple())
        self.assertLess(ds2.get_version_tuple(), ds3.get_version_tuple())

    def test_invalid_version_format_raises_error(self):
        """Non-semantic version format raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            DatasetRef(id="DS-013", label="Test", version="1.2")
        self.assertIn("major.minor.patch", str(cm.exception))

    def test_non_integer_version_components_raise_error(self):
        """Non-integer version components raise ValueError."""
        with self.assertRaises(ValueError) as cm:
            DatasetRef(id="DS-014", label="Test", version="1.2.x")
        self.assertIn("must be integers", str(cm.exception))

    def test_to_dict_includes_version_fields(self):
        """to_dict() includes version and parent_version."""
        ds = DatasetRef(id="DS-015", label="Test", version="2.1.0", parent_version="1.5.3")
        payload = ds.to_dict()
        self.assertEqual(payload["version"], "2.1.0")
        self.assertEqual(payload["parent_version"], "1.5.3")

    def test_from_dict_loads_version_fields(self):
        """from_dict() loads version and parent_version."""
        payload = {
            "id": "DS-016",
            "label": "Test",
            "created_at": "2025-12-07T10:00:00+00:00",
            "version": "3.2.1",
            "parent_version": "3.2.0",
        }
        ds = DatasetRef.from_dict(payload)
        self.assertIsNotNone(ds)
        self.assertEqual(ds.version, "3.2.1")
        self.assertEqual(ds.parent_version, "3.2.0")

    def test_from_dict_uses_default_version_if_missing(self):
        """from_dict() uses default version 1.0.0 if not provided."""
        payload = {
            "id": "DS-017",
            "label": "Test",
            "created_at": "2025-12-07T10:00:00+00:00",
        }
        ds = DatasetRef.from_dict(payload)
        self.assertIsNotNone(ds)
        self.assertEqual(ds.version, "1.0.0")
        self.assertIsNone(ds.parent_version)

    def test_major_bump_from_any_version(self):
        """Major bump works from any starting version."""
        test_cases = [
            ("0.1.0", "1.0.0"),
            ("1.0.0", "2.0.0"),
            ("3.7.12", "4.0.0"),
        ]
        for start, expected in test_cases:
            with self.subTest(start=start):
                ds = DatasetRef(id="DS-018", label="Test", version=start)
                ds_next = ds.bump_major()
                self.assertEqual(ds_next.version, expected)

    def test_minor_bump_from_any_version(self):
        """Minor bump works from any starting version."""
        test_cases = [
            ("0.0.1", "0.1.0"),
            ("1.0.0", "1.1.0"),
            ("3.7.12", "3.8.0"),
        ]
        for start, expected in test_cases:
            with self.subTest(start=start):
                ds = DatasetRef(id="DS-019", label="Test", version=start)
                ds_next = ds.bump_minor()
                self.assertEqual(ds_next.version, expected)

    def test_patch_bump_from_any_version(self):
        """Patch bump works from any starting version."""
        test_cases = [
            ("0.0.0", "0.0.1"),
            ("1.0.0", "1.0.1"),
            ("3.7.12", "3.7.13"),
        ]
        for start, expected in test_cases:
            with self.subTest(start=start):
                ds = DatasetRef(id="DS-020", label="Test", version=start)
                ds_next = ds.bump_patch()
                self.assertEqual(ds_next.version, expected)

    def test_version_immutability(self):
        """Original dataset unchanged after version bump."""
        ds = DatasetRef(id="DS-021", label="Test", version="1.2.3")
        original_version = ds.version
        original_parent = ds.parent_version
        
        ds.bump_major()
        
        # Original unchanged
        self.assertEqual(ds.version, original_version)
        self.assertEqual(ds.parent_version, original_parent)


if __name__ == "__main__":
    unittest.main()
