# labos/__init__.py

"""
LabOS Core Package

This package defines the foundational building blocks for ChemLearn LabOS:
- Experiments
- Jobs
- Datasets
- Audit logging
- Module registry / method provenance

Phase 0: skeleton only, no heavy logic. This is the spine the rest of the system
will grow around.
"""

from .core.experiments import Experiment
from .core.jobs import Job
from .core.datasets import DatasetRef
from .core.audit import AuditEvent
from .core.module_registry import ModuleMetadata, ModuleRegistry
from .core.signature import Signature

__all__ = [
    "Experiment",
    "Job",
    "DatasetRef",
    "AuditEvent",
    "ModuleMetadata",
    "ModuleRegistry",
    "Signature",
]
