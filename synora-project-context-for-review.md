# Synora — project context for ContextGuard

**Purpose of this file:** Give ContextGuard a concise, source-grounded description of the Synora project and a few open questions to review before a planning or kickoff meeting. This summary was prepared from the Synora `README.md`, `doc/PRD_ENTERPRISE.md`, `SYNORA_COMPLETE_SYSTEM_ARCHITECTURE.md`, and `plan.md`. It is not a release approval or a substitute for checking those original documents.

## Review goal

Are Synora's current project scope, shared-memory design, and next implementation priorities clear enough to plan the next development phase?

## Scope

Review the product and system direction described in the supplied project documents. Focus on input channels, project routing, memory and approval boundaries, and unresolved engineering readiness. Do not infer a release date, staffing commitment, or production readiness from this summary.

## What Synora is

Synora is a project-intelligence workspace. It is intended to turn project information from meetings, WhatsApp, and user-supplied files or notes into traceable evidence, project-scoped knowledge, and a visual Project Atlas built with Excalidraw.

The system is described as using one shared Synora agent and one shared memory engine. Projects provide context and authorization boundaries; they are not separate agents or isolated memory systems.

## Intended information flow

1. Ingest authorized project information, such as completed Google Meet transcripts, WhatsApp messages, or supported manual uploads.
2. Preserve the original source and provenance as evidence.
3. Resolve which project the information belongs to and extract candidate knowledge such as decisions, requirements, questions, and actions.
4. Keep ambiguous communication in Unknown Context for a person to route. Do not force uncertain information into a project.
5. Update project-scoped memory from evidence and retain state history.
6. Generate a structured visual plan and compile it into an Excalidraw Project Atlas.

## Requirements stated in the project documents

- Keep one shared agent and memory engine, with project boundaries on context and access.
- Preserve evidence provenance so derived knowledge can be traced to its source.
- Keep unresolved project routing out of a guessed project; provide a human triage path.
- Keep generated knowledge and proposed high-impact changes distinct from evidence and approved project state.
- Generate Excalidraw output from a structured visual plan through a deterministic compiler; do not let the model write arbitrary raw canvas JSON.
- Keep a history of project-state and visual changes.
- Treat Excalidraw as an output/read-only view in the system architecture; visual edits should not silently become source evidence.
- For completed meetings, preserve transcript, speaker, and timestamp provenance and reuse the shared evidence/memory pipeline.

## Questions to resolve before the next phase

1. Which input channels are actually in scope for the next release: Google Meet, Vexa-captured Meet, WhatsApp, manual uploads, or any others?
2. The README and system architecture describe Excalidraw as generated output, but the PRD's unified-input section lists Excalidraw as an ingestion channel. Is canvas input explicitly out of scope, or is the PRD describing a future capability?
3. The README describes routine evidence-backed memory updates as automatic, while the PRD describes human approval before high-impact state changes. Which types of update are automatic, and which require approval?
4. What concrete acceptance criteria define a successful next phase (for example, routing quality, evidence traceability, user review behavior, or visual revision correctness)?
5. Which items in `plan.md` marked as needing evaluation or migration review are gates for this phase, and who owns them?

## Important limits of this summary

- This file summarizes planning and architecture documents; it does not verify that every described feature is currently deployed or working.
- No delivery date, budget, assigned owners, or user-study result is asserted here.
- Treat the questions above as clarification prompts, not claims that the project is blocked.
