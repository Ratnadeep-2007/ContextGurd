---
doc: prd
status: approved
---
# ContextGuard — Product Requirements

Source: scope.md > The Core Loop and The POC Boundary; approved idea document sections 1, 3, 8, and 13. Visual constraints are from the current user request. Agent-selected details are implementation choices, not invented user testimony.

## The Core Journey
1. Open a calm workspace and start a review or load a clearly labeled fictional sample.
2. State the decision, optionally select a project for shared recall, add PDF/DOCX/text, inspect extraction and suggested criteria.
3. Run the review; see real stage progress, honest failures, and exact source-linked findings.
4. Inspect an issue, enter who can clarify it, then use one contextual answer dropdown. Other is last and opens a custom-answer field. Leave unanswered information open, dismiss an irrelevant finding, or explicitly record accepted risk.
5. Recheck, see what changed, undo a resolution, reopen the saved case, and copy/download a kickoff brief.

## Screens and Layout
One workspace with a slim navigation rail, page heading, goal/source setup, and report. Recent Reviews uses the available sidebar height. Providers & privacy is at the right of the top navbar. Findings list at left and evidence/action detail at right; stack on narrow screens. Sources, review criteria, history, and provider information have focused panels rather than extra app sections. A project-assigned review can display earlier same-project decisions with their original sources.

## Look and Feel
No gradients. Warm off-white canvas, white surfaces, deep green primary controls, readable charcoal type, muted issue colors. Clear typographic hierarchy, modest corners, no decorative dashboard charts or chatbot. Guide sentences accompany actions and remain available on mobile.

## Features and Behavior
### Sources and criteria
Preserve original passages with stable IDs and hashes. Show extraction failures and limits. Suggested criteria are optional; record exclusion reasons. Source edits invalidate stale results and resolutions. Goal is editable for live cases; fixture sample inputs remain fixed so replay is honest.
### Analysis and evidence
Three bounded roles return typed JSON. Verify quote existence and references, required check coverage, duplicate findings, and conflict evidence. Show semantic uncertainty; exact quote validation is not proof of truth. Readiness status never approves a project.
### Clarification and memory
Resolve only a selected issue; save answer/action/owner/reason and provenance. A user-confirmed answer is distinguishable from documentary proof. Unknown answers remain open. Undo restores open status. New source content reopens affected analysis.

Source answer choices must be supported by the cited quotations. Contextual handling choices are identified as user decisions and cannot be mistaken for extracted document facts. No answer is preselected for a new finding. The API validates choice IDs/actions; a selected source answer retains stable passage references and survives reload.

Explicit project membership of a review enables recall of earlier confirmed clarifications from that project. Historical answers include their original question/review, answer, owner, date and source quotes. They are context for reconfirmation, not automatic approval of new evidence. Undo, changed inputs, project changes and deletion remove a decision from active recall. Local keyword/recent retrieval is implemented; the Mem0 OSS REST connector is available, but no live Mem0 service is connected in the recorded environment.
### Useful output
Show side-by-side quotes and a selected-issue evidence map. Copy/download a brief including sources, unresolved questions, user assertions, exclusions, and limitations. Saved reviews can be reopened/deleted with explicit confirmation for deletion.

The brief separates recorded clarifications from open questions and accepted risks. It includes counts, selected answers and source locations, owners and earlier project context considered. All-clarified output does not certify project readiness. If an earlier decision used by a report changes or is removed, export requires a recheck.

## States and Boundaries
Empty: guide the first input or sample. Loading: show actual server stages. Missing keys: live review unavailable with setup guidance; sample remains usable. Failed parsing or inference: show actionable error and preserve inputs. No findings: show coverage and limitations. Local single-user storage retains the exact records. Live review sends excerpts to enabled model providers; if a Mem0 service is configured, confirmed answer text and project metadata can also be sent there for indexing. Index failure retains local recall.

## Product Decisions
Meta Muse Wonder primary; Groq first fallback; optional NVIDIA second fallback. Case memory and graph support the report. No automatic messages. Every action needs guidance.
## What We're Building
The complete local review loop, accessible responsive UI, provider adapters, regression/evaluation tests, setup and demo instructions.
## Deferred From the POC
Public multi-user hosting and authenticated sharing, external ticket/messaging integrations, scanned-document OCR, accounts/roles and collaborative assignment workflows. Names entered as owners are currently labels, not registered accounts or notifications.
## Non-Goals
Project management, truth certification, automatic project approval, or guaranteed error-free AI.
## Open Questions
An initial Muse Wonder run completed; current post-revision live quality still requires a successful run from a process with provider access. Real fallback account access and live Mem0 embeddings are unverified. User demand and formal user usability sessions remain unvalidated. Final user readiness confirmation is not recorded.

