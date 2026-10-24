---
doc: scope
status: approved
---
# ContextGuard

Approval basis: the user reviewed the refined idea and requested implementation on 23 October 2026. This document transcribes that existing context rather than claiming a new interview occurred.

## The Unique Kernel
Check evidence against a kickoff decision, expose meaningful uncertainties with real quotations, and update a report after user clarification.
## Who It's For
A project lead or freelancer preparing a development kickoff from a brief, requirements, meeting notes, and a task list.
## The Core Loop
State a goal → add sources → review checks and evidence → clarify or dismiss → recheck → copy a kickoff brief. Return when a source or decision changes.
## Inspiration & Identity
User direction: minimal, impressive, no gradients, no AI slop, every action has a guide sentence. Implementation choice: ivory, forest green, charcoal, restrained amber and red; editorial typography and clear rules.
## Why This Matters to the Learner
User asked to turn the researched ContextGuard idea into a complete working project with code review and tests.
## What "Working" Looks Like
The browser completes the fictional sample review, shows exact evidence, saves a clarification, updates its status, reopens the case, and copies a brief. Own documents use configured live providers; failures never masquerade as success.
## The POC Boundary
Local single-user web application, PDF/DOCX/text sources, source preview, editable suggested criteria, Planner/Evidence/Challenge, deterministic validation, SQLite case memory, user corrections and undo, evidence map, export and copy, fixed evaluation cases.
## Later
Public deployment, multi-user access control, richer parser/OCR, collaborative review.
## Explicitly Cut
Synora code reuse, messaging integrations, organization-wide unscoped memory, autonomous external actions, arbitrary readiness scores, guaranteed correctness, and fabricated live results.

## Accepted extension: project memory

The user explicitly required remembering earlier project reviews. Reviews now have an explicit project association, and confirmed clarifications can be recalled by another review in that same project. SQLite retains exact decisions and source provenance; the Mem0 OSS REST adapter can index them for retrieval. Active recall excludes undone, stale-input, deleted, and other-project decisions. Historical context does not automatically approve a new review. Local recall and controlled adapter/browser tests pass; a real Mem0 service is not running in this environment. See `docs/project-memory.md`.

