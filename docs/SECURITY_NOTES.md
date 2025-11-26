# Security Notes

This document tracks LabOS security considerations. Focus areas include safeguarding UI inputs, user-provided content, and execution paths that could expose the platform to malicious behaviors.

## UI Input Handling & User Data
- Perform **input sanitization and encoding** on any user-supplied values before rendering in the UI, persisting to logs, or passing into downstream services. Prefer allowlists for expected formats and escape content prior to display to prevent cross-site scripting or HTML/script injection.
- Treat **unsafe or untrusted content** (uploads, free-text fields, pasted code/snippets) as potentially hostile. Enforce size/type limits, strip active content where possible, and quarantine or reject inputs that include scripts, embedded HTML, or serialized objects that could trigger execution.
- **Avoid `eval`, `exec`, or dynamic code execution** on user-derived strings, configuration snippets, or data files. When execution-like behavior is required (e.g., expressions for filtering), rely on vetted parsers or constrained interpreters that validate grammar and block arbitrary code.
- Log validation failures and rejected content with enough context for auditing, but avoid echoing raw malicious payloads back to users. Tie sanitization and rejection decisions to `AuditEvent` records where applicable to keep a traceable security trail.
- Apply the same controls to background jobs and data ingestion paths as to UI forms to prevent bypassing client-side safeguards. Normalize and re-validate inputs server-side before use.

## Safe Defaults
- Disable or mock dangerous features in development/education modes so learners cannot accidentally trigger execution of arbitrary content.
- Keep third-party libraries that process user content (parsers, upload handlers) pinned to vetted versions and configured to reject unexpected MIME types or encodings.
- Document any known limitations or unsupported inputs so operators can warn users before data submission.
