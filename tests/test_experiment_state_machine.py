"""Tests for experiment state machine transitions."""

import unittest
from datetime import datetime

from labos.core.experiments import (
    Experiment,
    ExperimentStatus,
    InvalidStateTransitionError,
    VALID_TRANSITIONS,
)


class TestExperimentStateMachine(unittest.TestCase):
    """Test experiment status transition validation."""

    def test_draft_to_running_allowed(self):
        """DRAFT → RUNNING is valid transition."""
        exp = Experiment(id="EXP-001", name="Test", status=ExperimentStatus.DRAFT)
        exp.mark_running()
        self.assertEqual(exp.status, ExperimentStatus.RUNNING)

    def test_running_to_completed_allowed(self):
        """RUNNING → COMPLETED is valid transition."""
        exp = Experiment(id="EXP-002", name="Test", status=ExperimentStatus.RUNNING)
        exp.mark_completed()
        self.assertEqual(exp.status, ExperimentStatus.COMPLETED)

    def test_running_to_failed_allowed(self):
        """RUNNING → FAILED is valid transition."""
        exp = Experiment(id="EXP-003", name="Test", status=ExperimentStatus.RUNNING)
        exp.mark_failed()
        self.assertEqual(exp.status, ExperimentStatus.FAILED)

    def test_completed_to_archived_allowed(self):
        """COMPLETED → ARCHIVED is valid transition."""
        exp = Experiment(id="EXP-004", name="Test", status=ExperimentStatus.COMPLETED)
        exp.mark_archived()
        self.assertEqual(exp.status, ExperimentStatus.ARCHIVED)

    def test_failed_to_draft_allowed(self):
        """FAILED → DRAFT is valid (retry from failure)."""
        exp = Experiment(id="EXP-005", name="Test", status=ExperimentStatus.FAILED)
        exp.update_status(ExperimentStatus.DRAFT)
        self.assertEqual(exp.status, ExperimentStatus.DRAFT)

    def test_draft_to_completed_forbidden(self):
        """DRAFT → COMPLETED is invalid (must go through RUNNING)."""
        exp = Experiment(id="EXP-006", name="Test", status=ExperimentStatus.DRAFT)
        with self.assertRaises(InvalidStateTransitionError) as cm:
            exp.mark_completed()
        self.assertIn("Invalid transition", str(cm.exception))
        self.assertIn("draft", str(cm.exception).lower())
        self.assertIn("completed", str(cm.exception).lower())

    def test_draft_to_failed_forbidden(self):
        """DRAFT → FAILED is invalid."""
        exp = Experiment(id="EXP-007", name="Test", status=ExperimentStatus.DRAFT)
        with self.assertRaises(InvalidStateTransitionError):
            exp.mark_failed()

    def test_completed_to_running_forbidden(self):
        """COMPLETED → RUNNING is invalid (cannot restart completed experiment)."""
        exp = Experiment(id="EXP-008", name="Test", status=ExperimentStatus.COMPLETED)
        with self.assertRaises(InvalidStateTransitionError):
            exp.mark_running()

    def test_archived_to_any_forbidden(self):
        """ARCHIVED is terminal state - no transitions allowed."""
        exp = Experiment(id="EXP-009", name="Test", status=ExperimentStatus.ARCHIVED)
        
        with self.assertRaises(InvalidStateTransitionError):
            exp.mark_running()
        
        with self.assertRaises(InvalidStateTransitionError):
            exp.mark_completed()
        
        with self.assertRaises(InvalidStateTransitionError):
            exp.update_status(ExperimentStatus.DRAFT)

    def test_same_status_no_op(self):
        """Transitioning to same status is no-op."""
        exp = Experiment(id="EXP-010", name="Test", status=ExperimentStatus.RUNNING)
        old_updated_at = exp.updated_at
        exp.update_status(ExperimentStatus.RUNNING)
        self.assertEqual(exp.status, ExperimentStatus.RUNNING)
        # Should not update timestamp for no-op
        self.assertEqual(exp.updated_at, old_updated_at)

    def test_updated_at_changes_on_transition(self):
        """updated_at timestamp changes when status changes."""
        import time
        exp = Experiment(id="EXP-011", name="Test", status=ExperimentStatus.DRAFT)
        old_updated_at = exp.updated_at
        time.sleep(0.001)  # Ensure timestamp difference
        exp.mark_running()
        self.assertGreater(exp.updated_at, old_updated_at)

    def test_is_finished_includes_completed_and_failed(self):
        """is_finished() returns True for COMPLETED and FAILED."""
        exp1 = Experiment(id="EXP-012", name="Test", status=ExperimentStatus.COMPLETED)
        self.assertTrue(exp1.is_finished())
        
        exp2 = Experiment(id="EXP-013", name="Test", status=ExperimentStatus.FAILED)
        self.assertTrue(exp2.is_finished())

    def test_is_finished_false_for_active_states(self):
        """is_finished() returns False for DRAFT, RUNNING, ARCHIVED."""
        exp1 = Experiment(id="EXP-014", name="Test", status=ExperimentStatus.DRAFT)
        self.assertFalse(exp1.is_finished())
        
        exp2 = Experiment(id="EXP-015", name="Test", status=ExperimentStatus.RUNNING)
        self.assertFalse(exp2.is_finished())
        
        exp3 = Experiment(id="EXP-016", name="Test", status=ExperimentStatus.ARCHIVED)
        self.assertFalse(exp3.is_finished())

    def test_is_active_for_draft_and_running(self):
        """is_active() returns True for DRAFT and RUNNING."""
        exp1 = Experiment(id="EXP-017", name="Test", status=ExperimentStatus.DRAFT)
        self.assertTrue(exp1.is_active())
        
        exp2 = Experiment(id="EXP-018", name="Test", status=ExperimentStatus.RUNNING)
        self.assertTrue(exp2.is_active())

    def test_is_active_false_for_terminal_states(self):
        """is_active() returns False for COMPLETED, FAILED, ARCHIVED."""
        exp1 = Experiment(id="EXP-019", name="Test", status=ExperimentStatus.COMPLETED)
        self.assertFalse(exp1.is_active())
        
        exp2 = Experiment(id="EXP-020", name="Test", status=ExperimentStatus.FAILED)
        self.assertFalse(exp2.is_active())
        
        exp3 = Experiment(id="EXP-021", name="Test", status=ExperimentStatus.ARCHIVED)
        self.assertFalse(exp3.is_active())

    def test_valid_transitions_complete(self):
        """VALID_TRANSITIONS covers all statuses."""
        all_statuses = {
            ExperimentStatus.DRAFT,
            ExperimentStatus.RUNNING,
            ExperimentStatus.COMPLETED,
            ExperimentStatus.FAILED,
            ExperimentStatus.ARCHIVED,
        }
        self.assertEqual(set(VALID_TRANSITIONS.keys()), all_statuses)

    def test_archived_has_no_valid_transitions(self):
        """ARCHIVED status has empty transition list (terminal)."""
        self.assertEqual(VALID_TRANSITIONS[ExperimentStatus.ARCHIVED], [])


if __name__ == "__main__":
    unittest.main()
