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
- [x] Automated checks/code review and resulting repairs complete: latest 56 tests, clean cached dependency installation, actual Windows launcher/repeat launch/setup/live-check commands, nine grouped browser checks and inspected report/screenshots. Live model verification has since passed for Muse Wonder + Groq and the controlled-failure fallback (NVIDIA); live source-account verification (Vexa/Slack/WhatsApp) remains separately pending on user configuration.
- [ ] Learner feedback resolved and explicit readiness confirmed.
## Code Tour and App Map
- [x] Current implementation reference and static recap delivered in devpost/app-map.html: route/permission gate → verified goal review → authorized confirmation/export. This is an agent recap, not observed learner editor practice or personal reflection.
## Revisions
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
