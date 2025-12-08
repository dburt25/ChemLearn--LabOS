"""Tests for job retry mechanism."""

import unittest

from labos.core.jobs import Job, JobStatus


class TestJobRetry(unittest.TestCase):
    """Test job retry functionality."""

    def test_failed_job_can_retry(self):
        """FAILED job with retries remaining can_retry() → True."""
        job = Job(
            id="JOB-001",
            experiment_id="EXP-001",
            kind="test",
            status=JobStatus.FAILED,
            max_retries=3,
            retry_count=0,
        )
        self.assertTrue(job.can_retry())

    def test_max_retries_exhausted_cannot_retry(self):
        """Job at max retries cannot retry."""
        job = Job(
            id="JOB-002",
            experiment_id="EXP-001",
            kind="test",
            status=JobStatus.FAILED,
            max_retries=3,
            retry_count=3,
        )
        self.assertFalse(job.can_retry())

    def test_queued_job_cannot_retry(self):
        """QUEUED job cannot be retried (not failed yet)."""
        job = Job(
            id="JOB-003",
            experiment_id="EXP-001",
            kind="test",
            status=JobStatus.QUEUED,
        )
        self.assertFalse(job.can_retry())

    def test_running_job_cannot_retry(self):
        """RUNNING job cannot be retried."""
        job = Job(
            id="JOB-004",
            experiment_id="EXP-001",
            kind="test",
            status=JobStatus.RUNNING,
        )
        self.assertFalse(job.can_retry())

    def test_completed_job_cannot_retry(self):
        """COMPLETED job cannot be retried."""
        job = Job(
            id="JOB-005",
            experiment_id="EXP-001",
            kind="test",
            status=JobStatus.COMPLETED,
        )
        self.assertFalse(job.can_retry())

    def test_retry_increments_count(self):
        """retry() increments retry_count."""
        job = Job(
            id="JOB-006",
            experiment_id="EXP-001",
            kind="test",
            status=JobStatus.FAILED,
            retry_count=0,
        )
        job.retry()
        self.assertEqual(job.retry_count, 1)

    def test_retry_resets_status_to_queued(self):
        """retry() resets status to QUEUED."""
        job = Job(
            id="JOB-007",
            experiment_id="EXP-001",
            kind="test",
            status=JobStatus.FAILED,
        )
        job.retry()
        self.assertEqual(job.status, JobStatus.QUEUED)

    def test_retry_clears_error_message(self):
        """retry() clears error_message."""
        job = Job(
            id="JOB-008",
            experiment_id="EXP-001",
            kind="test",
            status=JobStatus.FAILED,
            error_message="Something went wrong",
        )
        job.retry()
        self.assertIsNone(job.error_message)

    def test_retry_clears_timestamps(self):
        """retry() clears started_at and finished_at."""
        job = Job(
            id="JOB-009",
            experiment_id="EXP-001",
            kind="test",
            status=JobStatus.FAILED,
        )
        job.start()
        job.finish(success=False, error="Test failure")
        
        self.assertIsNotNone(job.started_at)
        self.assertIsNotNone(job.finished_at)
        
        job.retry()
        
        self.assertIsNone(job.started_at)
        self.assertIsNone(job.finished_at)

    def test_retry_raises_if_not_failed(self):
        """retry() raises ValueError if job not FAILED."""
        job = Job(
            id="JOB-010",
            experiment_id="EXP-001",
            kind="test",
            status=JobStatus.QUEUED,
        )
        with self.assertRaises(ValueError) as cm:
            job.retry()
        self.assertIn("Cannot retry", str(cm.exception))
        self.assertIn("queued", str(cm.exception).lower())

    def test_retry_raises_if_max_retries_exceeded(self):
        """retry() raises ValueError if max retries reached."""
        job = Job(
            id="JOB-011",
            experiment_id="EXP-001",
            kind="test",
            status=JobStatus.FAILED,
            max_retries=2,
            retry_count=2,
        )
        with self.assertRaises(ValueError) as cm:
            job.retry()
        self.assertIn("Max retries", str(cm.exception))
        self.assertIn("2", str(cm.exception))

    def test_multiple_retries(self):
        """Job can be retried multiple times up to max_retries."""
        job = Job(
            id="JOB-012",
            experiment_id="EXP-001",
            kind="test",
            status=JobStatus.FAILED,
            max_retries=3,
            retry_count=0,
        )
        
        # First retry
        job.retry()
        self.assertEqual(job.retry_count, 1)
        self.assertEqual(job.status, JobStatus.QUEUED)
        
        # Fail again
        job.start()
        job.finish(success=False, error="Retry 1 failed")
        
        # Second retry
        job.retry()
        self.assertEqual(job.retry_count, 2)
        
        # Fail again
        job.start()
        job.finish(success=False, error="Retry 2 failed")
        
        # Third retry
        job.retry()
        self.assertEqual(job.retry_count, 3)
        
        # Fail again
        job.start()
        job.finish(success=False, error="Retry 3 failed")
        
        # Cannot retry again
        self.assertFalse(job.can_retry())
        with self.assertRaises(ValueError):
            job.retry()

    def test_max_retries_default_is_3(self):
        """Default max_retries is 3."""
        job = Job(
            id="JOB-013",
            experiment_id="EXP-001",
            kind="test",
        )
        self.assertEqual(job.max_retries, 3)

    def test_retry_count_default_is_0(self):
        """Default retry_count is 0."""
        job = Job(
            id="JOB-014",
            experiment_id="EXP-001",
            kind="test",
        )
        self.assertEqual(job.retry_count, 0)

    def test_to_dict_includes_retry_fields(self):
        """to_dict() includes max_retries and retry_count."""
        job = Job(
            id="JOB-015",
            experiment_id="EXP-001",
            kind="test",
            max_retries=5,
            retry_count=2,
        )
        payload = job.to_dict()
        self.assertEqual(payload["max_retries"], 5)
        self.assertEqual(payload["retry_count"], 2)

    def test_from_dict_loads_retry_fields(self):
        """from_dict() loads max_retries and retry_count."""
        payload = {
            "id": "JOB-016",
            "experiment_id": "EXP-001",
            "kind": "test",
            "status": "failed",
            "created_at": "2025-12-07T10:00:00+00:00",
            "max_retries": 5,
            "retry_count": 2,
        }
        job = Job.from_dict(payload)
        self.assertIsNotNone(job)
        self.assertEqual(job.max_retries, 5)
        self.assertEqual(job.retry_count, 2)

    def test_from_dict_uses_defaults_for_missing_retry_fields(self):
        """from_dict() uses defaults if retry fields missing."""
        payload = {
            "id": "JOB-017",
            "experiment_id": "EXP-001",
            "kind": "test",
            "status": "queued",
            "created_at": "2025-12-07T10:00:00+00:00",
        }
        job = Job.from_dict(payload)
        self.assertIsNotNone(job)
        self.assertEqual(job.max_retries, 3)
        self.assertEqual(job.retry_count, 0)


if __name__ == "__main__":
    unittest.main()
