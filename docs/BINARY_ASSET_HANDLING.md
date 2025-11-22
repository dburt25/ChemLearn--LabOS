# Binary Asset Handling

This guide explains how ChemLearn LabOS tracks large or binary artifacts produced in CODEX (or any external tooling) and keeps the GitHub repository healthy.

## Why Git LFS

GitHub blocks files larger than 100 MB in normal git history. Git Large File Storage (LFS) keeps lightweight pointers in the repo while pushing the actual binary payloads to LFS object storage. This prevents repository bloat and keeps clones fast.

## Prerequisites

1. Install Git LFS once on every machine or browser-based dev container that commits to this repo:
   ```powershell
   winget install Git.GitLFS
   git lfs install
   ```
2. Verify that `git lfs env` reports the expected version before committing binaries.

## Tracking Patterns

The repository-wide `.gitattributes` already tracks common binary extensions and the `artifacts/` and `datasets/` folders. If you generate a new type of binary, add another pattern to `.gitattributes` (same `filter=lfs diff=lfs merge=lfs -text` stanza) **before** committing it.

## Workflow From CODEX

1. Export the binary artifact from CODEX to your local workspace (or download it after CODEX builds the asset).
2. Place it under `artifacts/` (for model weights, compiled assets, etc.) or `datasets/` (for data drops). Keep transient scratch files under the ignored `artifacts/tmp/` or `data/tmp/` directories.
3. Stage files normally: `git add artifacts/model_v1.onnx`.
4. Git automatically stores them via LFS because of `.gitattributes`. Confirm with `git lfs ls-files`.
5. Commit and push as usual: `git commit -m "Add v1 inference weights"` followed by `git push`.

## Additional Tips

- Avoid storing secrets or personally identifiable data in binary artifacts.
- If a binary exceeds your account's LFS quota, prune old versions or use an external artifact bucket and keep only metadata in the repo.
- Keep a short README in each artifact subfolder describing provenance, generator version, and checksum, so reviewers understand what they are downloading.
