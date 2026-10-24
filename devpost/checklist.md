---
doc: checklist
status: approved
---
# Build Checklist

Build mode: fast, based on user's instruction to create the complete app, review it, and test it. Existing approval is carried forward; no invented new sign-off. October 24 audit update: the repository is now public at https://github.com/Ratnadeep-2007/ContextGurd, with consolidated commit 2b6df12. The original per-slice commit notes below describe the earlier build stage; no separate slice commits are claimed.

## Slices
- [x] **1. Review the sample and inspect grounded findings**
  Becomes usable: A complete browser-to-API-to-report loop with real source references and clear sample labeling.
  Why now: Proves the evidence-checking kernel early.
  PRD ref: `prd.md > Analysis and evidence`
  Spec ref: `spec.md > Components`
  Build: Scaffold, source models, sample fixture, verifier, API, report and source UI.
  Verify (mechanical): API regression tests, frontend build, sample browser flow.
  Learner check: Open the sample, read one issue and its sources.
  Commit: Included in consolidated initial commit 2b6df12. No separate slice commit is claimed.
- [x] **2. Clarify, reopen, undo, and copy the brief**
  Becomes usable: Case memory and output survive reloads and preserve distinctions between answers and evidence.
  Why now: Closes the user workflow.
  PRD ref: `prd.md > Clarification and memory`, `prd.md > Useful output`
  Spec ref: `spec.md > Data Model`
  Build: SQLite snapshots, history, per-issue action controls, reruns, exports, criteria exclusions.
  Verify (mechanical): Persistence/undo/staleness tests plus browser resolve/reload/export.
  Learner check: Confirm one answer, reopen, undo it, and inspect the brief.
  Commit: Included in consolidated initial commit 2b6df12. No separate slice commit is claimed.
- [x] **3. Review uploaded sources with configured live providers**
  Becomes usable: Own PDF/DOCX/text and honest live-provider availability/error handling.
  Why now: Reuses the proven kernel and memory flow.
  PRD ref: `prd.md > Sources and criteria`
  Spec ref: `spec.md > External Services and Dependencies`
  Build: Bounded parsing, typed provider calls, fallbacks, role orchestration, configuration UI.
  Verify (mechanical): Parsing, malicious input and provider/schema tests pass. An earlier real Muse Wonder run completed. The current live attempt uploaded three sources, then hit local network permission failures before a provider response.
  Learner check: Configure a provider locally, add documents, and run a review.
  Commit: Included in consolidated initial commit 2b6df12. No separate slice commit is claimed.

## Hands-on Checkpoints
- [x] Early usable behavior explored by user — the user supplied UI screenshots and requested clarification-form and navigation revisions, which were implemented and browser-checked.
- [ ] Final kick-the-tires exploration and feedback completed by user.
## Final Review
- [x] Agent code review and mechanical checks complete — latest evidence: 83 backend tests, frontend build, a new clean cached frontend reinstall/build, nine grouped browser checks, dedicated clarification/project-memory journeys and offline app-map verification. See evaluation/release-readiness.md for limits.
- [ ] Final user feedback resolved and learner confirms ready to ship.
## Code Tour and App Map
- [x] Reference app map generated and checked against actual paths and symbols.
- [x] Agent-provided static recap and current three-stop reference map delivered: the owner-first/single-dropdown requirement maps to UI, API/storage and verification/output, with actual test evidence. This is recorded as a static recap, not observed learner editor practice. Personal reflection is optional and was not collected.
## Revisions

- API port changed to 8017 because port 8000 was occupied; no existing service was stopped.
- Native HTML/CSS was sufficient for the selected-issue map; React Flow was not needed.
- Existing reviewed context and the implementation request provide approval; no interview answers or fresh sign-off were invented.
- Two independent code-review passes identified and repaired evidence, memory, stale-run, and navigation defects.
- Dependencies came from cached third-party npm packages because registry access was restricted. No Synora application source was copied.
- Slice 3 is implemented. An initial real Muse Wonder run completed and exposed issues; later repairs pass controlled regression tests. Final updated live quality and final user-led review remain pending. A checked implementation slice does not claim those external checks passed.

## Current submission audit

See `compliance-audit.md` and `evaluation/release-readiness.md`. Required planning files and an MIT license are published. The local PRD/spec consistency pass and static learning recap are now prepared. A public demo-video link, learner-written submission/exit-survey completion and final readiness confirmation are not recorded as complete. Roles/accounts and automatic assignment remain proposals. Current audit fixes/documents require a new local/public checkpoint; earlier history is not rewritten.

## Release-audit repairs

- [x] Keep pytest bootstrap/recovery away from the normal review database.
- [x] Decouple API tests from frontend build output; recognize incomplete production builds.
- [x] Preserve broken virtual environments and verify that Windows launcher behavior.
- [x] Audit public repository/history/index/worktree and refresh factual technical documentation/app map.
- [ ] Verify current live analysis from a process allowed to reach providers; this session's attempt was blocked by Windows network permissions.

