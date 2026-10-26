---
doc: checklist
status: approved
---
# Build Checklist
Execution follows the user's explicit implementation instruction; no separate approval interview is invented. User feedback stays separate from automated checks.

## Slices
- [x] **1. Ingest authorized evidence and confirm routing**
  Becomes usable: Accounts, projects, manual sources and routing contracts; the later conversation-first revision replaces the Unknown Context UI.
  Why now: Authorization/routing must precede memory.
  PRD ref: `prd.md > Evidence and routing`
  Spec ref: `spec.md > Shared contracts and routing`
  Build: Contracts, transactions, identity, sources, routing, revisions and segments.
  Verify (mechanical): Explicit/mapped/unknown/unauthorized routes, dedup/edit and segment provenance tests.
  Learner check: Select a project, import a note and inspect the retained project passages; unmatched input must not enter project memory.
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
  Learner check: Try fictional input, connection controls and the report; share feedback.
  Commit: `Add isolated source adapters and local review interface`.

- [x] **4. Implement conversation-first capture and project reviews**
  Becomes usable: Automatic source registration, complete-input project matching, filtered reviews, role-aware resolution and consolidated Word/Markdown output.
  Why now: The user approved this direction and explicitly requested implementation after reviewing the earlier registration UI.
  PRD ref: The Core Journey, Evidence and routing, Sources.
  Spec ref: Components, Shared contracts and routing, Data Model.
  Build: Private background intake/status/retry, deterministic coverage/access/source-map gates, successful-run unmatched removal, project source grants, connection-only Sources and the review workspace/export flow.
  Verify (mechanical): 89 tests, nine grouped fictional browser journeys with zero page errors, real downloads/parsed Word text, all four existing test accounts, 390px screenshots, module syntax checks, Windows startup/reuse and credential scan passed. The new fictional live prompt was attempted but blocked by outbound Windows permissions; no live certification is claimed.
  Learner check: Run start.bat under the normal Windows account and use its printed address, try the sample, inspect a project match, confirm an answer and download the updated document. Actual learner feedback remains pending.
  Commit: `Implement conversation-first project reviews and source connections`.

## Current Verification Status
- October 26: processing/network follow-up passed 42 targeted Python tests, six Node UI tests and four grouped isolated progress-browser checks. The preceding UI verification also passed all 12 existing grouped browser journeys. These are separate recorded suites, not a new full-suite aggregate.
- Latest real Synora sample review failed at 0/82 passages due to local outbound network denial. An earlier sample attempt failed citation validation after analysis. Historical provider successes do not establish current end-to-end success.
- The offline-account server was stopped with no active jobs. Normal startup is now guarded; the next step is a normal-user start.bat launch, Retry retained input, and inspection of resulting citations and exports.
- Fixes are saved locally. Git metadata is read-only in this session, so these revisions are not committed or published.

## Hands-on Checkpoints
- [ ] Learner tries the fresh app and supplies feedback.
## Final Review
- [x] Earlier implementation checks completed; their dated evidence is retained under Revisions. Current targeted processing/network checks are recorded above. This checkbox does not certify the failed live sample or real connector accounts.
- [ ] Complete a normal-user live sample retry, inspect every displayed citation and exported output, and repair any remaining validation failure.
- [ ] Learner feedback resolved and explicit readiness confirmed.
## Code Tour and App Map
- [x] Current implementation reference and static recap delivered in devpost/app-map.html: route/permission gate → verified goal review → authorized confirmation/export. This is an agent recap, not observed learner editor practice or personal reflection.
## Revisions
- Selected Graphite & Cobalt reference (October 26, 2026): user explicitly chose the generated 01 image. Replaced Amber with a dark sidebar/light workspace/cobalt palette, question-first report, stacked ruled source blocks and a compact filter/resolution layout. Fixed review-opening scroll position. Twelve existing isolated browser journeys, six processing tests and dedicated desktop/tablet/mobile reference checks passed; final visual comparison is recorded in design-qa.md. Real data and decision authority are unchanged.
- Claude Amber light correction (October 26, 2026): user explicitly requested white rather than black. Kept the terracotta accent and square controls; changed navigation/background/cards/inputs and status colors to light-mode values. Current theme tokens and checks are documented in docs/claude-amber-theme.md.
- Claude Amber palette (October 26, 2026): user supplied and selected a palette reference. Sampled its eight color tokens and separated semantic theme styles into web/theme.css, retaining native Segoe UI, square corners, flat fills and existing workflow. All 12 isolated browser journeys passed with zero page errors; desktop/mobile screenshots and computed palette/square-corner/no-gradient checks passed. Verification is recorded in docs/claude-amber-theme.md; earlier UI concepts remain design explorations.
- Clean retest / duplicate prevention (October 26, 2026): user requested removal of test data and one ticket per underlying issue. Added citation-preserving consolidation, unchanged-review reuse, stable failed-intake retry review IDs and failed status on rejected citations. Full Python suite, eight focused tests and 12 grouped isolated browser journeys pass. Reset utility preserves users/projects/setup and refuses active jobs. Live reset subsequently completed after both jobs failed: captured sources, evidence, intakes, reviews and decision memory are empty; users/projects/setup remain. Normal server restart is required to load the duplicate-prevention code. See docs/conflict-deduplication.md.
- Typography refinement (October 26, 2026): user requested a different font. All interface text now uses native Segoe UI Variable Text / Segoe UI, including headings, fields and quotations; numeric processing counters use tabular figures. Windows Segoe UI availability verified; no remote font dependency introduced. Existing bundled DM Sans assets remain unused.
- Workbench redesign (October 26, 2026): user requested a new theme and layout without gradients or rounded components. Replaced ivory/sage/serif styling with charcoal navigation, paper work surfaces, cobalt actions, square geometry, consistent sans-serif headings and divided review rows. Backend behavior and user records are preserved. All 12 controlled browser journeys passed with zero page errors; desktop/mobile screenshots were inspected and computed styles on Project Reviews, Sources and Team verified square corners/no gradients. Learner feedback remains pending. See docs/workbench-theme.md.
- Documentation reconciliation (October 26, 2026): aligned scope, PRD, spec, checklist and app map with visible processing, per-attempt timing, bounded batching/retries and the offline-account launch guard. Historical verification remains dated; the failed live sample, connector acceptance and learner sign-off remain open. No new product scope or learner participation is invented.
- Network/timer follow-up (October 26, 2026): confirmed the agent-launched server inherited CodexSandboxOffline network restrictions and stopped it with no active jobs. The launcher now rejects that identity for server startup; retries receive a persisted fresh start time, and legacy timing has an honest label. 42 targeted Python tests, six UI tests and four browser journeys passed. User must launch start.bat from File Explorer and retry; live model/citation success remains unverified.
- Processing visibility (October 26, 2026): learner requested an immediate visible state while documents process. Added prominent status, live stages/counts/elapsed updates, reload restoration, duplicate prevention and result/retry actions. Mechanical checks passed: four Node tests, four grouped progress-browser checks and 12 existing browser journeys. User retry/feedback remains pending; final readiness is not claimed. See docs/processing-ui.md.
- Current written brief supersedes earlier minimal scope; technical implementation is authorized, live service success is not assumed.
- Slice 1: eight routing/authorization tests passed. The default Windows pytest temporary directory was inaccessible; verification uses a fresh artifact-local temporary directory. No user data was touched.
- Slice 2: 18 tests pass, including source citation rejection, provider/schema fallback, decision authority, supersession, unknown answers and explicit different milestone guards. Provider tests use controlled HTTP only.
- Slice 3/final audit: 43 tests passed in the fresh .venv, actual start.bat and seven grouped real-Edge checks passed with fictional input. Controlled Slack OAuth uses a test protector because real DPAPI was denied; no live connector/model certification is claimed. docs/verification.md records exact boundaries.
- User-requested local setup follow-up: model settings migrated privately into ignored .env, launcher setup/status/browser/port handling improved, API tests explicitly avoid loading real .env, and 49 tests passed. No provider/source calls or publication were performed.
- User-requested UI refinement: independently align with the original outer ContextGuard's ivory/sage/serif visual language; add selected finding/detail, filters and mobile workspace navigation. Nine grouped browser checks pass; docs/ui-refresh.md records screenshot evidence and standard third-party asset licenses. Final learner approval remains open.
- Separate requested live checks attempted Muse Wonder/Groq/NVIDIA using fictional text only. Windows blocked all outbound connections before an HTTP response (10013); Vexa/Slack accounts are unconfigured and Baileys pairing remains disabled.
- Added repeatable scripts/verify_live.py and explicit start.bat --live-check, with isolated verification storage, real-provider schema/citation/report checks, guarded selected-source ingestion and safe failure diagnostics. All 55 automated tests pass; real source credentials, selected meeting/channel and a verified live WhatsApp pairing flow remain outstanding.
- Live follow-up (Oct 24, 2026, normal user session): the earlier 10013 denial was isolated to the sandboxed agent session; direct provider connections succeed without proxy changes. Muse Wonder and Groq verify independently with human-reviewed findings; the controlled primary-failure → real fallback path verifies via NVIDIA; NVIDIA-as-primary exceeds the 35s bounded timeout (≈80s probe, truncated output) and stays fallback-only. Groq quota intermittency (8,000 tokens/min observed) diagnosed; one bounded transient retry per provider added (56 tests). Synthetic DPAPI round trip passes in the normal session. Vexa/Slack named blockers confirmed via --sources (no external contact); Baileys upstream remains 7.0.0-rc14 prerelease, so live pairing stays isolated pending a stable pinned runtime, protected session design and user QR pairing with a selected chat.
- User decisions (Oct 24, 2026): final hands-on trial deferred ("not tried yet") — Final Review learner confirmation stays open. User requested guided setup for Vexa and Slack (local .env only). User explicitly accepted the Baileys prerelease/unofficial-service risk and will QR-pair a selected chat when a safe read-only flow exists. Dependency feasibility rechecked: `baileys@7.0.0-rc14` installs and imports cleanly on Node v24.18.0 in a throwaway probe (not added to the repo). Live pairing is still NOT implemented or verified: it remains a dedicated build slice requiring the user present to scan the QR code, a selected-chat allowlist enforced before retention, DPAPI-protected session state at rest, and explicit connect/disconnect controls.
- Vexa local setup (Oct 25, 2026): user has no payment card, so the hosted API path was dropped. The pre-existing self-hosted Vexa v012 stack on this machine was reused (no install, no payment): dedicated ContextGuard key (bot+tx scopes) minted locally and wired into the ignored `.env`, scope validation passed (bots/status 200; transcript read authorized), deployment STT is the local CPU Whisper service, and ContextGuard was restarted reporting Vexa configured. Scoped-key support (98bc28b) preceded this. Remaining: one real fictional meeting test with the user present; Slack still awaits guided OAuth setup.

- Current conversation-first implementation is recorded in docs/conversation-workflow.md and docs/conversation-verification.md. Registration and Unknown Context UI are removed; source/role boundaries, disposal, retry and exports are mechanically checked. Older 8027 is preserved and updated startup reuses 8028. Final learner readiness remains open.
