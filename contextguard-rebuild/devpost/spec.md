---
doc: spec
status: approved
---
# ContextGuard — Technical Specification
Authority: current user instruction authorizes implementation and derived engineering choices. This is not a claimed historical interview.

## How This Works, In Plain Language
Independent readers normalize sources. Complete input is staged in a private intake job. An ordered model pass proposes project-specific units; deterministic coverage, scope and provenance checks gate project evidence and memory. Per-project analysis produces citation-verified findings. Only successful complete processing removes unmatched input. A failed run retains it for retry. Human responses and separate authorized confirmation create versioned decisions; reports and consolidated Word/Markdown files are exported independently of original uploads.

## The Core Journey Through the System
Browser → authorized capture → private intake → complete-unit routing/coverage → project evidence → goal/provider analysis → citation verification → successful unmatched-input disposal → filtered reviews → assignment/response/authorized confirmation → versioned decisions → report or Word/Markdown document. PRD ref: The Core Journey.

## Stack
Python 3.11+, FastAPI/Pydantic v2/httpx/SQLite, native HTML/CSS/JS, pypdf and python-docx. This fresh implementation avoids another frontend build service. Existing installed third-party packages may run tests; no prior app code/schema is imported. Optional Baileys worker supports experimental QR pairing and selected text; package installation and real account verification remain pending.

## Where It Runs and How Someone Tries It
Double-click `start.bat` from File Explorer under the normal Windows account and use its printed address. The launcher checks ports and reuses a compatible rebuild instance; do not assume a fixed port. Direct `python scripts/serve.py` is a developer entry point. Normal launcher startup rejects the actual CodexSandboxOffline Windows identity, whose outbound connections are restricted; `--check` and `--live-check` are separate diagnostic paths and are not covered by that startup guard. Access logs are disabled to keep OAuth callback codes out of logs. README documents first account, fictional demo and optional services. No deployment or publication.

## Look and Feel
Selected Graphite & Cobalt reference: background #f3f4f7, card #ffffff, sidebar #20252d, border #d2d8e2, primary #2549a2, foreground #202735 and selection #eaf0fc. The exact image selected by the user supersedes both Claude Amber variants. At 1536px the sidebar is 280px and the report index approximately 35% of its workspace; stacked source passages and a compact resolution grid follow the reference. See docs/graphite-cobalt-theme.md and design-qa.md. `web/theme.css` supplies semantic color tokens separately from responsive structure in `web/style.css`. Native Segoe UI Variable Text / Segoe UI is used for body and display headings, with Tahoma/Arial/system sans-serif fallbacks. Square borders, no gradients or decorative shadows, responsive evidence/finding columns, native controls and brief guidance. Never reveal credentials/session values.

The user-requested visual alignment adds native Segoe UI for all headings/body text and unchanged Lucide library icons (ISC), all served from the same origin. `web/views.js` owns the independent presentation, imported as a native browser module by `web/app.js`; no frontend build service is required. A selected-finding/filter view replaces repeated full report forms. Keyboard selection, mobile drawer/Escape and focus restoration are browser-checked. See docs/ui-refresh.md and bundled resource licenses.

## Components
Conversation-first processing is implemented in `app/intake.py` and `app/intake_api.py`; [the current workflow](../docs/conversation-workflow.md) records verified behavior and limits. `ThreadPoolExecutor` workers permit status polling without holding a database transaction during model calls. `app/exports.py` generates deterministic consolidated documents. `web/workspace.js` and `web/app.js` provide capture, connections, processing status and review filtering. Legacy source/routing APIs preserve compatibility; their former registration/inbox UI is removed.

### Shared contracts and routing
Pydantic evidence/finding/citation/route envelopes; explicit eligible projects → approved mapping constraints → validated model route, or unmatched disposal after success. No project memory is read for unmatched input. Batches cover each input unit exactly once, using exact offsets and quoted text. Full input is bounded at 60,000 characters/1,000 units, with an explicit failure rather than truncation. Project evidence has separate source grants; complete raw mixed-project inputs never appear in state/poll responses. Source/item identity deduplicates events and preserves revisions. Source/profile changes during matching cause a retained-input retry. PRD refs: Evidence and routing, Identity and source access.
### Processing status and retries
`web/processing.js` renders an immediate upload state, server stages, stage-specific counters, elapsed time, completion/retry actions and scoped history above the capture cards. `web/app.js` restores active jobs through polling and blocks duplicate capture while the current project is processing. `units_processed/units_total` measure routing coverage, not review completion; `analysis_done/analysis_total` describe analysis batches. Poll failures show reconnecting. Failed uploads preserve form selections; failed intake retains input.

Each new intake stores `attempt=1` and `attempt_started`; explicit retry or duplicate resubmission of failed input increments the attempt, resets progress and starts a fresh clock without changing `created`. Legacy records are not rewritten: their timer is labelled Since original upload until retried. Network-denial failures include normal-user startup guidance without exposing keys. See [processing verification](../docs/processing-ui.md) and [network recovery](../docs/windows-network-recovery.md).

### Identity and workflow
PBKDF2 passwords, opaque expiring cookie sessions, same-origin mutation guards, workspace/project/source permissions. Review owners assign/dismiss; assignees respond; project owners/decision_owners confirm immutable decision versions. PRD ref: Assignment and resolution.
### Review and providers
Environment-configured OpenAI-compatible Muse Wonder/Groq/NVIDIA interface, bounded inputs, shared schemas, exact quotes and scope/version guard. No guessed primary endpoint or automatic fixture fallback. SQLite project decisions are the shared memory. Source changes invalidate snapshots. Routing batches use up to 25 units and an 8,000-character text budget; analysis uses an 8,000-character evidence budget. These are text budgets, not guarantees on the total provider request size. HTTP 413 triggers recursive batch splitting rather than resending the same oversized batch; an unsplittable passage fails with retained-input guidance. Transient HTTP 429/500/502/503/504 and timeouts have at most three attempts per provider; Retry-After is bounded at 30 seconds. Other connection failures proceed to configured fallbacks. All fallback output still passes schema and citation checks. PRD ref: Goal-specific findings.
### Finding identity and review reuse
`ProposedFinding.issue_key` is optional for compatibility and requested from the model for cross-batch grouping. `Reviews.duplicate_issue` checks comparison metadata and title version labels before using stable keys, normalized titles or conservative overlapping-evidence similarity. `merge_issue` retains exact citations, references, priority and related questions. Reviews carry an analysis signature; unchanged successful authorized reviews are reused. Intake-scoped retries reuse their saved project review ID unless human responses prohibit replacement. `scripts/reset_test_content.py` provides an explicit transaction-based test-content reset with active-job protection. See [verification and limits](../docs/conflict-deduplication.md).

### Source adapters
Manual parsing, Vexa REST, Slack OAuth/selected pulls and experimental read-only Baileys pairing/event/manual-import boundary. Explicit network consent; bounded timeouts, redacted failures and retry information. No live claim from contract tests. PRD ref: Sources.

## Data Model
SQLite `records(kind,id,workspace,body)` entities include user, session, project, source, source_event, evidence, mapping, review, decision, oauth_state, intake and connection_check. A process lock/transaction serializes writes, never provider requests. Raw intake is staged for processing/retry; success retains exact project evidence and removes unmatched staging. Historical evidence revisions and append-only decisions remain. Sources share project memory.

## File Structure
`app/{contracts,storage,service,providers,adapters,api}.py`, `web/`, `tests/`, `samples/`, `docs/`, `devpost/`.

`scripts/launcher.py` provides local dependency/configuration/port checks, safe `.env` creation, browser readiness and repeat-launch reuse. `start.bat` selects supported Python and delegates to it; `scripts/serve.py` starts the local app without access logs. `start.bat --check` performs setup checks without starting a server or contacting external providers. Tests use `create_app(load_settings=False)` to avoid loading real keys.

## External Services and Dependencies
Vexa POST /bots and GET /transcripts/{platform}/{native_meeting_id}, X-API-Key. Slack oauth.v2.access, conversations.info/history/replies and chat.getPermalink with conversation read/history scopes, no send scopes. Baileys unofficial MIT prerelease is isolated as a private stdio worker with encrypted sessions, no history sync and an explicit selected-chat allowlist; real pairing remains unverified. Models use environment URLs/models/keys. See docs/integration-research.md for current primary sources and drift. Keys never enter prompts/logs/source control.

## Important Failure Modes
Unauthorized/ambiguous routing denies or holds evidence; incomplete transcript/parse/connection failures stay visible; provider failures have no fabricated result; edits/deletions invalidate report/confirmation/export; unavailable Baileys dependencies or Windows key protection block pairing and leave manual import available.

## What Was Simplified and Why
One local process/SQLite and native browser UI reduce Windows setup. Slack uses explicit bounded pulls with visible incomplete coverage rather than unattended subscriptions. Core memory is a deterministic versioned decision record; a future semantic index must obey the same access/routing boundary.

## Decisions and Open Issues
Current direction replaces earlier connector/team deferrals. Source authorization outranks similarity. Live-model verification (fictional documents) passed October 24, 2026 for Muse Wonder and Groq independently and for the controlled-failure fallback via NVIDIA; NVIDIA as an isolated primary exceeded the bounded 35s timeout and is treated as fallback-only within current bounds. The current working tree supersedes the earlier one-retry policy with at most three attempts per provider and a 30-second Retry-After cap. This documents implemented behavior, not proof of a successful new live sample review. Real-account tests (Vexa meeting, Slack workspace, WhatsApp pairing) remain separately required and blocked on user-supplied local configuration. No personal learning uncertainty has been reported; tests demonstrate the permission/routing boundary. Local updates only.


## Latest Verification and Remaining Work
October 26, 2026: 42 targeted Python tests, six progress UI tests and four grouped isolated progress-browser checks passed. The previous UI pass also completed all 12 existing grouped browser journeys. These runs use controlled providers and isolated storage; counts are separate suites, not an asserted full-suite total. The launcher guard was exercised under the actual offline account. The latest six-document live run failed before routing because outbound connections were denied; an earlier run failed citation validation after analysis. A normal-user retry, citation/output inspection and real Vexa/Slack/WhatsApp account acceptance remain pending.

## Current WhatsApp direction

Experimental live Baileys pairing is implemented as a separate private Node worker with QR authorization, explicitly selected chats, text-only bounded ingestion and manual-export fallback. Sources manages pairing/selection; Project Reviews processes selected live text against Current project. No full-history sync or send/reply capability is exposed. Local session credentials require AES-GCM encryption and a Windows DPAPI-protected vault key; protection failure blocks pairing. Pending duplicate/edit/delete events are handled; already captured reviews remain evidence snapshots and are not automatically updated by later WhatsApp edits/deletes. Runtime installation, an actual phone scan, reconnect and native dependency behavior remain live-verification requirements. Current session npm/DPAPI access was denied. See docs/whatsapp-live.md and docs/baileys-research.md; earlier disabled-runtime statements are superseded by this section, not evidence of a verified connection.
