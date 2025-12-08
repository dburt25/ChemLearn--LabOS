# Module Registration Standards

## Overview
LabOS modules use `ModuleDescriptor` to register operations with the module registry. This document standardizes naming, versioning, and registration patterns across all modules.

## Module Identifier Standards

### Naming Convention
Module identifiers follow a hierarchical dot-notation:
- Format: `<domain>[.<subdomain>].<module>`
- Examples:
  - `spectroscopy` (top-level domain)
  - `pchem.calorimetry` (physical chemistry subdomain)
  - `ei_ms.basic_analysis` (electron ionization mass spectrometry)
  - `import.wizard` (data import utilities)

### Identifier Consistency
- Use **MODULE_KEY** or **MODULE_ID** constant (standardize on `MODULE_KEY`)
- Must be globally unique within the LabOS ecosystem
- Use lowercase with underscores for multi-word components
- Avoid abbreviations unless domain-standard (e.g., `ei_ms`, `nmr`, `ir`)

## Version Standards

### Semantic Versioning
All modules follow [Semantic Versioning 2.0.0](https://semver.org/):
- Format: `MAJOR.MINOR.PATCH`
- MAJOR: Breaking API changes
- MINOR: Backward-compatible feature additions
- PATCH: Backward-compatible bug fixes
- Examples: `0.2.0`, `0.3.1`, `1.0.0`

### Version Constant
- Use **MODULE_VERSION** or **VERSION** constant (standardize on `MODULE_VERSION`)
- Start at `0.1.0` for new modules
- Phase 2 modules typically at `0.2.x` (active development)
- Reserve `1.0.0` for production-ready, validated modules

## Registration Pattern

### Standard Template
```python
"""Module docstring with purpose and scope."""

from __future__ import annotations

from typing import Mapping

from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor

MODULE_KEY = "domain.module_name"
MODULE_VERSION = "0.2.0"
DESCRIPTION = "Brief module purpose (1-2 sentences)."


def operation_handler(params: Mapping[str, object]) -> dict[str, object]:
    """Execute module operation.
    
    Args:
        params: Operation parameters (module-specific schema)
    
    Returns:
        Result dictionary with status, data, and metadata
    """
    # Implementation
    return {"status": "success", "data": {}}


def _register() -> None:
    """Register module descriptor and operations with global registry."""
    descriptor = ModuleDescriptor(
        module_id=MODULE_KEY,
        version=MODULE_VERSION,
        description=DESCRIPTION,
    )
    descriptor.register_operation(
        ModuleOperation(
            name="operation_name",
            description="Brief operation purpose.",
            handler=operation_handler,
        )
    )
    register_descriptor(descriptor)


# Call registration at module import time
_register()
```

### Registration Best Practices
1. **Encapsulate registration** in `_register()` function
2. **Call at module import** with `_register()` at module level
3. **Use constants** for module_id, version, description (enables reuse)
4. **Clear operation names**:
   - Prefer domain verbs: `analyze`, `compute`, `import`, `export`
   - Legacy stubs use `*_stub` suffix for clarity
5. **Document handler signatures** with type hints and docstrings

## Operation Standards

### Operation Naming
- Use **imperative verbs**: `analyze`, `compute`, `import`, `validate`
- Multiple operations OK: `analyze_nmr_spectrum`, `analyze_ir_spectrum`
- Legacy/stub operations: `nmr_stub`, `ir_stub` (mark as legacy in description)
- Aliases permitted for compatibility: `compute` → `analyze`

### Handler Contract
All operation handlers must:
- Accept `params: Mapping[str, object]` parameter
- Return `dict[str, object]` (or `Mapping[str, object]`)
- Include `status` field in result: `"success"`, `"failed"`, `"pending"`
- Handle missing params gracefully (use defaults or raise clear errors)
- Log errors internally, don't let exceptions bubble uncaught

### Parameter Schema
Document expected parameters in handler docstring:
```python
def run_analysis(params: Mapping[str, object]) -> dict[str, object]:
    """Run EI-MS analysis.
    
    Expected params:
        precursor_mass (float): Parent ion m/z value
        fragment_masses (list[float]): Fragment peak positions
        fragment_intensities (list[float], optional): Peak intensities
        annotations (dict, optional): Peak annotations
        
    Returns:
        Result dict with keys:
            status (str): "success" or "failed"
            analysis (dict): Annotated spectrum data
            metadata (dict): Provenance information
    """
```

## Module Audit Checklist

When reviewing or creating a module, verify:
- ☐ Module identifier follows dot-notation standard
- ☐ `MODULE_KEY` constant defined at top of file
- ☐ `MODULE_VERSION` follows semantic versioning
- ☐ `DESCRIPTION` is concise (1-2 sentences)
- ☐ `_register()` function encapsulates descriptor creation
- ☐ `_register()` called at module level (not in `__main__`)
- ☐ All operations have clear `name` and `description`
- ☐ Handlers accept `Mapping[str, object]` params
- ☐ Handlers return `dict[str, object]` results
- ☐ Handler docstrings document expected params
- ☐ Result includes `status` field
- ☐ Operation names use domain-standard verbs

## Current Module Inventory

| Module ID | Version | Operations | Status | Notes |
|-----------|---------|------------|--------|-------|
| `spectroscopy` | 0.2.0 | analyze_nmr_spectrum, analyze_ir_spectrum, nmr_stub, ir_stub | ✅ Active | Legacy stubs + primary operations |
| `pchem.calorimetry` | 0.2.0 | compute | ✅ Active | Educational stub |
| `ei_ms.basic_analysis` | 0.2.1 | analyze, compute (alias) | ✅ Active | Dual operations for compatibility |
| `import.wizard` | 0.3.0 | compute | ✅ Active | Schema inference helper |
| `eims.fragmentation` | 0.2.0 | compute | ⚠️ Legacy | Forwards to ei_ms.basic_analysis |

## Migration Notes

### Inconsistencies to Resolve
1. **Constant naming**: Some use `MODULE_ID`, others `MODULE_KEY` → Standardize on `MODULE_KEY`
2. **Version naming**: Some use `VERSION`, others `MODULE_VERSION` → Standardize on `MODULE_VERSION`
3. **Registration pattern**: spectroscopy registers inline, others use `_register()` → All should use `_register()`

### Recommended Actions
- **Phase 2.5.4**: Refactor spectroscopy module to use `_register()` function
- **Phase 2.5.4**: Deprecate `eims.fragmentation` module (legacy shim)
- **Phase 3**: Add module schema validation tests
- **Phase 3**: Create module scaffolding tool (`labos new module <name>`)

## See Also
- `labos/modules/__init__.py` - Module registry implementation
- `labos/core/module_registry.py` - Metadata registry
- `SWARM_STATUS.md` - Phase roadmap and bot slots
- `tests/test_module_registry.py` - Registration tests
