"""Hardened JSON storage primitives used by registry classes.

Storage layout
==============
- Each record is stored as an individual ``<id>.json`` file beneath a
  caller-specified base directory.
- Callers are expected to treat the base directory as a flat namespace;
  subdirectories are not traversed.
- Backup files use ``.backup.<n>`` suffix for rotation (configurable depth).

File format
===========
- Files contain a single JSON object.
- ``save`` writes prettified JSON with atomic temp-file + replace pattern.
- Checksum validation (SHA-256) is performed on load to detect corruption.

Concurrency & Safety
====================
- File locking (platform-adaptive) prevents race conditions during writes.
- Backup rotation preserves N previous versions before overwriting.
- Atomic writes ensure interrupted processes don't leave partial records.

Error handling expectations
===========================
- Missing directories are created automatically.
- Missing files raise ``NotFoundError`` when explicitly loaded.
- Bulk iteration helpers skip malformed or partial files with a logged
  warning so callers can tolerate corrupted state while continuing to load
  valid records.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import platform
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, TypeVar

from .core.errors import NotFoundError, RegistryError


logger = logging.getLogger(__name__)
T = TypeVar("T")

# Platform-specific file locking
_WINDOWS = platform.system() == "Windows"
if _WINDOWS:
    try:
        import msvcrt  # type: ignore
    except ImportError:  # pragma: no cover - Windows-only
        msvcrt = None  # type: ignore
else:
    try:
        import fcntl  # type: ignore
    except ImportError:  # pragma: no cover - Unix-only
        fcntl = None  # type: ignore


@contextlib.contextmanager
def _file_lock(file_handle):
    """Cross-platform file locking context manager."""
    
    if _WINDOWS and msvcrt:
        try:
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            # Lock failed, retry with timeout
            max_retries = 10
            for _ in range(max_retries):
                try:
                    msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RegistryError("Failed to acquire file lock after retries")
        try:
            yield
        finally:
            try:
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:  # pragma: no cover - cleanup safety
                pass
    elif fcntl:
        try:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            # Lock failed, retry with timeout
            max_retries = 10
            for _ in range(max_retries):
                try:
                    fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RegistryError("Failed to acquire file lock after retries")
        try:
            yield
        finally:
            try:
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
            except OSError:  # pragma: no cover - cleanup safety
                pass
    else:
        # No locking available (test environments or exotic platforms)
        yield


def _compute_checksum(data: bytes) -> str:
    """Compute SHA-256 checksum of byte content."""
    return hashlib.sha256(data).hexdigest()


class JSONFileStore:
    """Persist records as individual JSON files with hardened safety guarantees.
    
    Features:
    - Atomic writes via temp file + replace
    - Platform-adaptive file locking (fcntl on Unix, msvcrt on Windows)
    - Backup rotation (configurable depth)
    - SHA-256 checksum validation on load
    - Automatic corruption recovery from backups
    """

    def __init__(self, base_dir: Path, backup_depth: int = 3) -> None:
        """Initialize storage with backup rotation.
        
        Args:
            base_dir: Root directory for JSON files
            backup_depth: Number of backup versions to retain (0 to disable)
        """
        self.base_dir = base_dir
        self.backup_depth = backup_depth
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _record_path(self, record_id: str) -> Path:
        return self.base_dir / f"{record_id}.json"

    def _backup_path(self, record_id: str, index: int) -> Path:
        return self.base_dir / f"{record_id}.json.backup.{index}"

    def _checksum_path(self, record_id: str) -> Path:
        return self.base_dir / f"{record_id}.json.sha256"

    def _rotate_backups(self, record_id: str) -> None:
        """Rotate backup files, keeping only backup_depth most recent versions."""
        
        if self.backup_depth <= 0:
            return
        
        destination = self._record_path(record_id)
        if not destination.exists():
            return
        
        # Shift existing backups: .backup.N -> .backup.N+1
        for i in range(self.backup_depth - 1, 0, -1):
            old_backup = self._backup_path(record_id, i)
            new_backup = self._backup_path(record_id, i + 1)
            if old_backup.exists():
                old_backup.replace(new_backup)
        
        # Current file becomes .backup.1
        backup_1 = self._backup_path(record_id, 1)
        try:
            destination.replace(backup_1)
        except OSError:  # pragma: no cover - race condition safety
            pass

    def save(self, record_id: str, payload: Dict[str, Any]) -> None:
        """Save record with atomic write, locking, and backup rotation."""
        
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            destination = self._record_path(record_id)
            tmp_path = destination.with_suffix(destination.suffix + ".tmp")
            lock_path = destination.with_suffix(".lock")
            
            # Serialize payload
            json_bytes = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            checksum = _compute_checksum(json_bytes)
            
            # Acquire lock and rotate backups
            with open(lock_path, "w") as lock_file:
                with _file_lock(lock_file):
                    self._rotate_backups(record_id)
                    
                    # Write temp file atomically
                    tmp_path.write_bytes(json_bytes)
                    
                    # Write checksum
                    checksum_path = self._checksum_path(record_id)
                    checksum_path.write_text(checksum, encoding="utf-8")
                    
                    # Atomic replace
                    tmp_path.replace(destination)
            
            # Clean up lock file
            try:
                lock_path.unlink()
            except OSError:  # pragma: no cover - cleanup best-effort
                pass
                
        except OSError as exc:  # pragma: no cover - disk failure scenario
            raise RegistryError(f"Failed to persist record {record_id}: {exc}") from exc

    def load(self, record_id: str, verify_checksum: bool = True) -> Dict[str, Any]:
        """Load record with optional checksum verification and backup recovery.
        
        Args:
            record_id: Identifier for the record
            verify_checksum: If True, validate SHA-256 checksum (default: True)
            
        Returns:
            Deserialized JSON payload
            
        Raises:
            NotFoundError: Record not found
            RegistryError: Corruption detected and no valid backups available
        """
        
        path = self._record_path(record_id)
        if not path.exists():
            raise NotFoundError(f"Record {record_id} missing under {self.base_dir}")
        
        def _try_load(file_path: Path) -> Dict[str, Any] | None:
            """Attempt to load and validate a single file."""
            try:
                json_bytes = file_path.read_bytes()
                
                if verify_checksum:
                    expected_checksum_path = self._checksum_path(record_id)
                    if expected_checksum_path.exists():
                        expected = expected_checksum_path.read_text(encoding="utf-8").strip()
                        actual = _compute_checksum(json_bytes)
                        if actual != expected:
                            logger.warning(
                                "Checksum mismatch for %s: expected %s, got %s",
                                file_path, expected, actual
                            )
                            return None
                
                return json.loads(json_bytes.decode("utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load %s: %s", file_path, exc)
                return None
        
        # Try primary file
        result = _try_load(path)
        if result is not None:
            return result
        
        # Try backups in order (without checksum verification for backups)
        if self.backup_depth > 0:
            logger.warning("Primary file corrupted, attempting backup recovery for %s", record_id)
            for i in range(1, self.backup_depth + 1):
                backup_path = self._backup_path(record_id, i)
                if backup_path.exists():
                    # Backups are validated by structure only, not checksum
                    try:
                        json_bytes = backup_path.read_bytes()
                        result = json.loads(json_bytes.decode("utf-8"))
                        logger.info("Recovered %s from backup %d", record_id, i)
                        # Restore backup as primary
                        try:
                            self.save(record_id, result)
                        except RegistryError:  # pragma: no cover - recovery safety
                            pass
                        return result
                    except (json.JSONDecodeError, OSError) as exc:
                        logger.warning("Backup %d for %s also corrupted: %s", i, record_id, exc)
        
        raise RegistryError(
            f"Record {record_id} is corrupted and no valid backups available"
        )

    def list_ids(self) -> Iterable[str]:
        for file in sorted(self.base_dir.glob("*.json")):
            yield file.stem

    def load_all(self, loader: Callable[[Dict[str, Any]], T | None] | None = None) -> List[T | Dict[str, Any]]:
        """Load all JSON payloads in the base directory.

        A ``loader`` callable may be provided to validate/convert each raw
        mapping. When supplied, any record that raises an exception or returns
        ``None`` is skipped after emitting a warning.
        """

        records: List[T | Dict[str, Any]] = []
        for file in sorted(self.base_dir.glob("*.json")):
            try:
                payload: Dict[str, Any] = json.loads(file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                logger.warning("Skipping corrupted record %s: %s", file, exc)
                continue

            if loader is None:
                records.append(payload)
                continue

            try:
                processed = loader(payload)
            except Exception as exc:  # pragma: no cover - validation guardrail
                logger.warning("Skipping record %s due to loader error: %s", file, exc)
                continue
            if processed is None:
                logger.warning("Skipping record %s due to validation failure", file)
                continue
            records.append(processed)
        return records
