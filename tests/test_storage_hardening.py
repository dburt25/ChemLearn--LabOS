"""Tests for hardened JSON storage features (locking, backups, checksums)."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from labos.core.errors import NotFoundError, RegistryError
from labos.storage import JSONFileStore


class StorageHardeningTests(unittest.TestCase):
    """Verify file locking, backup rotation, and checksum validation."""

    def test_save_creates_backup_rotation(self):
        """Verify backup files are created and rotated correctly."""
        with TemporaryDirectory() as tmpdir:
            store = JSONFileStore(Path(tmpdir), backup_depth=3)
            
            # Save initial version
            store.save("record1", {"version": 1})
            self.assertTrue((Path(tmpdir) / "record1.json").exists())
            
            # Save v2 - should create .backup.1
            store.save("record1", {"version": 2})
            backup_1 = Path(tmpdir) / "record1.json.backup.1"
            self.assertTrue(backup_1.exists())
            loaded_backup = json.loads(backup_1.read_text())
            self.assertEqual(loaded_backup["version"], 1)
            
            # Save v3 - should shift backups
            store.save("record1", {"version": 3})
            backup_2 = Path(tmpdir) / "record1.json.backup.2"
            self.assertTrue(backup_2.exists())
            loaded_backup_2 = json.loads(backup_2.read_text())
            self.assertEqual(loaded_backup_2["version"], 1)

    def test_checksum_validation_detects_corruption(self):
        """Verify checksum mismatch triggers recovery from backup."""
        with TemporaryDirectory() as tmpdir:
            store = JSONFileStore(Path(tmpdir), backup_depth=2)
            
            # Save v1
            store.save("record2", {"data": "version1"})
            
            # Save v2 (creates backup of v1)
            store.save("record2", {"data": "version2"})
            
            # Corrupt the primary file ONLY
            record_path = Path(tmpdir) / "record2.json"
            record_path.write_text('{"data": "corrupted"}', encoding="utf-8")
            
            # Load should detect checksum mismatch and recover from backup
            result = store.load("record2", verify_checksum=True)
            # Should recover from backup.1 (which contains version1)
            self.assertEqual(result["data"], "version1")

    def test_load_without_checksum_skips_validation(self):
        """Verify checksum validation can be disabled for legacy files."""
        with TemporaryDirectory() as tmpdir:
            store = JSONFileStore(Path(tmpdir), backup_depth=0)
            
            # Write file manually without checksum
            record_path = Path(tmpdir) / "record3.json"
            record_path.write_text('{"data": "legacy"}', encoding="utf-8")
            
            # Should load successfully without checksum
            result = store.load("record3", verify_checksum=False)
            self.assertEqual(result["data"], "legacy")

    def test_backup_depth_zero_disables_rotation(self):
        """Verify backup_depth=0 disables backup creation."""
        with TemporaryDirectory() as tmpdir:
            store = JSONFileStore(Path(tmpdir), backup_depth=0)
            
            store.save("record4", {"version": 1})
            store.save("record4", {"version": 2})
            
            backup_1 = Path(tmpdir) / "record4.json.backup.1"
            self.assertFalse(backup_1.exists())

    def test_missing_record_raises_not_found(self):
        """Verify NotFoundError for missing records."""
        with TemporaryDirectory() as tmpdir:
            store = JSONFileStore(Path(tmpdir))
            
            with self.assertRaises(NotFoundError):
                store.load("nonexistent")

    def test_corrupted_record_without_backups_raises_error(self):
        """Verify RegistryError when primary and all backups are corrupted."""
        with TemporaryDirectory() as tmpdir:
            store = JSONFileStore(Path(tmpdir), backup_depth=1)
            
            # Save valid record
            store.save("record5", {"data": "valid"})
            
            # Corrupt primary file
            record_path = Path(tmpdir) / "record5.json"
            record_path.write_text('invalid json{', encoding="utf-8")
            
            # Corrupt backup
            backup_path = Path(tmpdir) / "record5.json.backup.1"
            if backup_path.exists():
                backup_path.write_text('invalid json{', encoding="utf-8")
            
            # Delete checksum to force JSON decode attempt
            checksum_path = Path(tmpdir) / "record5.json.sha256"
            if checksum_path.exists():
                checksum_path.unlink()
            
            # Should raise RegistryError
            with self.assertRaises(RegistryError):
                store.load("record5", verify_checksum=False)

    def test_atomic_write_prevents_partial_records(self):
        """Verify tmp + replace pattern ensures atomic writes."""
        with TemporaryDirectory() as tmpdir:
            store = JSONFileStore(Path(tmpdir))
            
            # Save record
            store.save("record6", {"size": "large" * 100})
            
            # Verify no .tmp files left behind
            tmp_files = list(Path(tmpdir).glob("*.tmp"))
            self.assertEqual(len(tmp_files), 0)
            
            # Verify record loads correctly
            result = store.load("record6")
            self.assertIn("size", result)

    def test_load_all_skips_corrupted_files(self):
        """Verify load_all handles corrupted files gracefully."""
        with TemporaryDirectory() as tmpdir:
            store = JSONFileStore(Path(tmpdir))
            
            # Create valid record
            store.save("valid", {"status": "ok"})
            
            # Create corrupted file manually
            corrupt_path = Path(tmpdir) / "corrupt.json"
            corrupt_path.write_text('not valid json{', encoding="utf-8")
            
            # load_all should skip corrupt and return valid
            results = store.load_all()
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["status"], "ok")


if __name__ == "__main__":
    unittest.main()
