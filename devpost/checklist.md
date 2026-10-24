---
doc: checklist
status: approved
---
# Build Checklist

Build mode: fast, based on user's instruction to create the complete app, review it, and test it. Existing approval is carried forward; no invented new sign-off. No git initialization/commits yet because the workspace is not a repository and no user instruction requires them.

## Slices
- [x] **1. Review the sample and inspect grounded findings**
  Becomes usable: A complete browser-to-API-to-report loop with real source references and clear sample labeling.
  Why now: Proves the evidence-checking kernel early.
  PRD ref: `prd.md > Analysis and evidence`
  Spec ref: `spec.md > Components`
  Build: Scaffold, source models, sample fixture, verifier, API, report and source UI.
  Verify (mechanical): API regression tests, frontend build, sample browser flow.
  Learner check: Open the sample, read one issue and its sources.
  Commit: Not made; repository initialization not requested.
- [x] **2. Clarify, reopen, undo, and copy the brief**
  Becomes usable: Case memory and output survive reloads and preserve distinctions between answers and evidence.
  Why now: Closes the user workflow.
  PRD ref: `prd.md > Clarification and memory`, `prd.md > Useful output`
  Spec ref: `spec.md > Data Model`
  Build: SQLite snapshots, history, per-issue action controls, reruns, exports, criteria exclusions.
  Verify (mechanical): Persistence/undo/staleness tests plus browser resolve/reload/export.
  Learner check: Confirm one answer, reopen, undo it, and inspect the brief.
  Commit: Not made; repository initialization not requested.
- [x] **3. Review uploaded sources with configured live providers**
  Becomes usable: Own PDF/DOCX/text and honest live-provider availability/error handling.
  Why now: Reuses the proven kernel and memory flow.
  PRD ref: `prd.md > Sources and criteria`
  Spec ref: `spec.md > External Services and Dependencies`
  Build: Bounded parsing, typed provider calls, fallbacks, role orchestration, configuration UI.
  Verify (mechanical): Parsing, malicious input, provider fallback/schema tests; live calls pending keys.
  Learner check: Configure a provider locally, add documents, and run a review.
  Commit: Not made; repository initialization not requested.

## Hands-on Checkpoints
- [ ] Early usable behavior explored by user — app will be left running for review.
- [ ] Final kick-the-tires exploration and feedback completed by user.
## Final Review
- [x] Agent code review and mechanical checks complete — 39 backend tests, frontend build, clean frontend reinstall, nine grouped browser checks. See evaluation/results.md for external checks still pending.
- [ ] Final user feedback resolved and learner confirms ready to ship.
## Code Tour and App Map
- [x] Reference app map generated and checked against actual paths and symbols.
- [ ] User learning activity/reflection (not performed; do not claim completion).
## Revisions

- API port changed to 8017 because port 8000 was occupied; no existing service was stopped.
- Native HTML/CSS was sufficient for the selected-issue map; React Flow was not needed.
- Existing reviewed context and the implementation request provide approval; no interview answers or fresh sign-off were invented.
- Two independent code-review passes identified and repaired evidence, memory, stale-run, and navigation defects.
- Dependencies came from cached third-party npm packages because registry access was restricted. No Synora application source was copied.
- Slice 3 is implemented and tested with controlled responses; actual provider access/live quality and final user-led review remain pending. A checked implementation slice does not claim those external checks passed.

