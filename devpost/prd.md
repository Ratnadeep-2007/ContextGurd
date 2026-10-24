---
doc: prd
status: approved
---
# ContextGuard — Product Requirements

Source: scope.md > The Core Loop and The POC Boundary; approved idea document sections 1, 3, 8, and 13. Visual constraints are from the current user request. Agent-selected details are implementation choices, not invented user testimony.

## The Core Journey
1. Open a calm workspace and start a review or load a clearly labeled fictional sample.
2. State the decision, add PDF/DOCX/text, inspect extraction and suggested criteria.
3. Run the review; see real stage progress, honest failures, and exact source-linked findings.
4. Inspect an issue, leave an answer/owner, add context, dismiss with a reason, or leave it unresolved.
5. Recheck, see what changed, undo a resolution, reopen the saved case, and copy/download a kickoff brief.

## Screens and Layout
One workspace with a slim navigation rail, page heading, goal/source setup, and report. Findings list at left and evidence/action detail at right; stack on narrow screens. Sources, review criteria, history, and provider information have focused panels rather than extra app sections.

## Look and Feel
No gradients. Warm off-white canvas, white surfaces, deep green primary controls, readable charcoal type, muted issue colors. Clear typographic hierarchy, modest corners, no decorative dashboard charts or chatbot. Guide sentences accompany actions and remain available on mobile.

## Features and Behavior
### Sources and criteria
Preserve original passages with stable IDs and hashes. Show extraction failures and limits. Suggested criteria are optional; record exclusion reasons. Source edits invalidate stale results and resolutions. Goal is editable for live cases; fixture sample inputs remain fixed so replay is honest.
### Analysis and evidence
Three bounded roles return typed JSON. Verify quote existence and references, required check coverage, duplicate findings, and conflict evidence. Show semantic uncertainty; exact quote validation is not proof of truth. Readiness status never approves a project.
### Clarification and memory
Resolve only a selected issue; save answer/action/owner/reason and provenance. A user-confirmed answer is distinguishable from documentary proof. Unknown answers remain open. Undo restores open status. New source content reopens affected analysis.
### Useful output
Show side-by-side quotes and a selected-issue evidence map. Copy/download a brief including sources, unresolved questions, user assertions, exclusions, and limitations. Saved reviews can be reopened/deleted with explicit confirmation for deletion.

## States and Boundaries
Empty: guide the first input or sample. Loading: show actual server stages. Missing keys: live review unavailable with setup guidance; sample remains usable. Failed parsing or inference: show actionable error and preserve inputs. No findings: show coverage and limitations. All content is local single-user storage except excerpts sent to configured providers for live inference.

## Product Decisions
Meta Muse Wonder primary; Groq first fallback; optional NVIDIA second fallback. Case memory and graph support the report. No automatic messages. Every action needs guidance.
## What We're Building
The complete local review loop, accessible responsive UI, provider adapters, regression/evaluation tests, setup and demo instructions.
## Deferred From the POC
Public multi-user hosting and authenticated sharing, integrations, scanned-document OCR, collaborative ownership workflows.
## Non-Goals
Project management, truth certification, automatic project approval, or guaranteed error-free AI.
## Open Questions
Actual primary/fallback availability and quality require credentials. User demand and user usability sessions remain unvalidated. These do not block implementing and testing the local app and adapters.

