# 3D Visualization Plan (Draft)

Plan for immersive visualization of molecular structures and simulations.

## Goals
- Provide intuitive 3D views for learners and researchers.
- Support headset and browser-based rendering pathways.

## Requirements
- Standardized data formats (e.g., PDB, CIF).
- Rendering pipeline that logs interactions for auditability.

## Data Contract for Future 3D Visualization Modules
- **Inputs**
  - PDB/CIF file path or object storage URI for the primary structure.
  - Optional ligand bundle: identifier, residue range, and display style hints for docking overlays.
  - Simulation snapshots: collection of frame IDs or timestamps plus the dataset or object store where frames live.
  - Optional annotation overlays: 2D SVG/PNG layers (e.g., from the Workspace tool) and a set of reference coordinates that align the overlay to the 3D view.
- **Outputs**
  - `DatasetRef` with `kind="3d-structure"` including metadata keys:
    - `source_uri`: where the structure/snapshots were loaded from.
    - `structure_format`: `pdb`, `cif`, or `trajectory`.
    - `ligands`: list of ligand identifiers and placement hints when provided.
    - `frame_ids`: array of snapshot IDs used for playback.
    - `annotations`: optional list of overlay artifact IDs (coming from the Workspace) plus coordinate anchors.
  - UI renderers consume the `DatasetRef` to choose an engine (web canvas vs. headset) and to register audit events about what was inspected or highlighted.

## Workspace Interop
- The Workspace/Drawing Tool will accept 2D notes and annotated overlays (images or SVG once the canvas ships) and let users tag them to Experiment IDs.
- Future docking/3D viewers will accept a `DatasetRef` ID; Workspace artifacts will pass their Experiment ID so the 3D module can fetch related overlays.
- No heavy visualization dependencies yet; the contract above keeps inputs/outputs predictable while the rendering stack is evaluated.

## Future Tasks
- Evaluate open-source visualization engines.
- Design accessibility features (colorblind-safe palettes, subtitles).
