---
doc: checklist
status: approved
---
# Build Checklist
Execution follows the user's explicit implementation instruction; no separate approval interview is invented. User feedback stays separate from automated checks.

## Slices
- [x] **1. Ingest authorized evidence and confirm routing**
  Becomes usable: Accounts, projects, manual sources and Unknown Context.
  Why now: Authorization/routing must precede memory.
  PRD ref: `prd.md > Evidence and routing`
  Spec ref: `spec.md > Shared contracts and routing`
  Build: Contracts, transactions, identity, sources, routing, revisions and segments.
  Verify (mechanical): Explicit/mapped/unknown/unauthorized routes, dedup/edit and segment provenance tests.
  Learner check: Import a note and route an unknown passage.
  Commit: `Build evidence ingestion and confirmed project routing`.
- [x] **2. Review a goal and confirm human decisions**
  Becomes usable: Verified findings, assignments, responses, memory and export.
  Why now: Proves the kernel before external connectors.
  PRD ref: `prd.md > Assignment and resolution`
  Spec ref: `spec.md > Review and providers`
  Build: Providers, citations, status rules, human authority and versioned memory.
  Verify (mechanical): True/false conflicts, exact quotes, unresolved answers, scope isolation and stale reports.
  Learner check: Inspect both passages, respond and confirm as decision owner.
  Commit: `Build goal review and versioned human decisions`.
- [x] **3. Run adapter controls and local browser workflow**
  Becomes usable: Manual documents, isolated source adapters and full report UI.
  Why now: Reuses the verified common pipeline.
  PRD ref: `prd.md > Sources`
  Spec ref: `spec.md > Source adapters`
  Build: Vexa/Slack clients, Baileys test/import boundary, launcher, privacy/setup and fictional sample.
  Verify (mechanical): HTTP contracts and full browser workflow; live accounts separately pending.
  Learner check: Try fictional input, inbox and report; share feedback.
  Commit: `Add isolated source adapters and local review interface`.

## Hands-on Checkpoints
- [ ] Learner tries the fresh app and supplies feedback.
## Final Review
- [x] Automated checks/code review and resulting repairs complete: latest 49 tests, clean cached dependency installation, actual Windows launcher/repeat launch/setup check, seven grouped browser checks and inspected report/screenshots. Live service verification is separately pending.
- [ ] Learner feedback resolved and explicit readiness confirmed.
## Code Tour and App Map
- [x] Current implementation reference and static recap delivered in devpost/app-map.html: route/permission gate → verified goal review → authorized confirmation/export. This is an agent recap, not observed learner editor practice or personal reflection.
## Revisions
- Current written brief supersedes earlier minimal scope; technical implementation is authorized, live service success is not assumed.
- Slice 1: eight routing/authorization tests passed. The default Windows pytest temporary directory was inaccessible; verification uses a fresh artifact-local temporary directory. No user data was touched.
- Slice 2: 18 tests pass, including source citation rejection, provider/schema fallback, decision authority, supersession, unknown answers and explicit different milestone guards. Provider tests use controlled HTTP only.
- Slice 3/final audit: 43 tests passed in the fresh .venv, actual start.bat and seven grouped real-Edge checks passed with fictional input. Controlled Slack OAuth uses a test protector because real DPAPI was denied; no live connector/model certification is claimed. docs/verification.md records exact boundaries.
- User-requested local setup follow-up: model settings migrated privately into ignored .env, launcher setup/status/browser/port handling improved, API tests explicitly avoid loading real .env, and 49 tests passed. No provider/source calls or publication were performed.
