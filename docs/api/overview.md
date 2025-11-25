# External API & ML Integration Overview

This package defines **interfaces only** for connecting LabOS to external model
providers. No network clients or vendor SDKs are included. Future implementers
should provide concrete subclasses that satisfy these contracts while keeping
all side-effects isolated from LabOS core modules.

## Interfaces

- `AbstractModelClient`: Minimal contract for submitting generic prediction
  payloads and returning a normalized `ModelPrediction` object.
- `ExternalSpectrumPredictor`: Specialization for spectrum generation or peak
  prediction, using a structured `SpectrumRequest` input.
- `ExternalPropertyPredictor`: Specialization for molecular property
  predictions powered by `PropertyRequest` inputs.

## Implementation Guidance

1. **Keep dependencies local**: Place vendor-specific code in a separate module
   that imports the interfaces from `labos.api`. Do not add transport libraries
   to LabOS core.
2. **Normalize I/O**: Validate inputs, map provider responses into
   `ModelPrediction`, and preserve any provider payloads in `raw_response` for
   auditability.
3. **Error handling**: Raise `ModelClientError` for validation, serialization,
   and provider rejections. Use `ModelTimeoutError` when a call exceeds a caller
   supplied or default timeout. Expose more granular subclasses only if they
   inherit from `ModelClientError`.
4. **Resource management**: Implement `close()` to release sessions or sockets.
   Make it safe to call multiple times.
5. **Provenance**: Populate `model_name`, `request_id`, and `metadata` so jobs
   and audit logs can trace predictions back to the underlying provider and
   configuration.

## Usage Sketch

```python
from labos.api import ExternalPropertyPredictor, PropertyRequest

class ExamplePropertyClient(ExternalPropertyPredictor):
    def predict(self, *, inputs, tags=None, timeout_s=None):
        ...  # translate generic inputs to provider call

    def predict_properties(self, request: PropertyRequest, *, timeout_s=None):
        ...  # convert request to provider payload and wrap response

    def close(self):
        ...  # close sessions
```

Implementations should include their own lightweight validation to prevent
malformed requests from reaching external services and to ensure audit logs stay
consistent across providers.
