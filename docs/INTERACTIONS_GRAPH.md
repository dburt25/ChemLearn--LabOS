# Interactions Graph

High-level view of how LabOS components communicate.

## Nodes (Placeholders)
-- LabOS Core
-- Scientific Modules
-- UI Control Panel
-- Data Services
-- Audit & Compliance Services

## Edges
-- Core ↔ Modules: capability APIs, validation callbacks.
-- Core ↔ Data: experiment/job/dataset persistence.
-- Core ↔ Audit: append-only log writes and queries.
-- UI ↔ Core: command routing and telemetry displays.
-- Modules ↔ Data: controlled dataset access mediated by Core.

## Future Work
-- Replace text with diagram once tooling available.
-- Annotate edges with protocols (REST, CLI, events) per phase.
