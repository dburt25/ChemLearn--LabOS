# labos/core/__init__.py

"""
Core domain objects for LabOS.

These classes are intentionally lightweight "records" that:
- Capture parameters
- Are easy to log and serialize
- Are compatible with ALCOA+ style audit trails later

They are NOT yet tied to any database or external system.
"""

from .experiments import Experiment
from .jobs import Job
from .datasets import DatasetRef
from .audit import AuditEvent, record_event
from .module_registry import ModuleMetadata, ModuleRegistry
from .signature import Signature
from .workflows import (
    WorkflowResult,
    attach_dataset_to_job,
    create_experiment,
    create_experiment_with_job,
    log_event_for_job,
    run_module_job,
)

__all__ = [
    "Experiment",
    "Job",
    "DatasetRef",
    "AuditEvent",
    "record_event",
    "ModuleMetadata",
    "ModuleRegistry",
    "Signature",
    "WorkflowResult",
    "create_experiment",
    "attach_dataset_to_job",
    "create_experiment_with_job",
    "log_event_for_job",
    "run_module_job",
]

