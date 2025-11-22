# System Invariants

Immutable principles that every ChemLearn LabOS component must respect.

## Faith & Ethics
1. Truth above profit in every feature, metric, and communication.
2. Service-first design prioritizing accessibility and equitable learning.

## Compliance & Auditability
1. All actions are logged with ALCOA+ discipline (Attributable, Legible, Contemporaneous, Original, Accurate + Complete, Consistent, Enduring).
2. Every computation must be reproducible with documented parameters and deterministic seeds.
3. Regulatory frameworks (FDA 21 CFR Part 11, ISO 13485/14971, IEC 62304, HIPAA/GDPR) inform architecture choices.

## Safety & Reproducibility
1. Experiments and jobs require explicit IDs, context, and versioned assets.
2. No feature may silently mutate data; provenance chains are mandatory.
3. Default posture is "explainable by design"—no black-box operations without justification.

## Swarm Collaboration
1. Bots work within their declared scope and leave clear traces (docs, CHANGELOG, validation notes).
2. Phase transitions require documented readiness checks and sign-off artifacts.
