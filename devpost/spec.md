---
doc: spec
status: approved
---
# ContextGuard — Technical Specification
Authority: current user instruction authorizes implementation and derived engineering choices. This is not a claimed historical interview.

## How This Works, In Plain Language
Independent readers normalize sources. A permission/routing gate stores confirmed project evidence or Unknown Context. Reviews snapshot evidence and prior decisions. A provider proposes structured findings; schema and exact quote checks reject invalid claims. Human responses and separate authorized confirmation create versioned decisions.

## The Core Journey Through the System
Browser → authenticated API → adapter → common evidence validation → routing → SQLite → goal review/provider → citation verification → stored report → assignment/response/decision confirmation → Markdown export. PRD ref: The Core Journey.

## Stack
Python 3.11+, FastAPI/Pydantic v2/httpx/SQLite, native HTML/CSS/JS, pypdf and python-docx. This fresh implementation avoids another frontend build service. Existing installed third-party packages may run tests; no prior app code/schema is imported. Optional Baileys bridge is disabled pending verification.

## Where It Runs and How Someone Tries It
`start.bat`, or `python scripts/serve.py` (equivalent to `python -m uvicorn app.run:app --host 127.0.0.1 --port 8027 --no-access-log`). New app uses 8027; original 8017 process is untouched. Access logs are disabled to keep OAuth callback codes out of logs. README documents first account, fictional demo and optional services. No deployment or publication.

## Look and Feel
Ivory page, white panels, forest actions, amber uncertainty, red errors, locally bundled body typography and serif display headings, responsive evidence/finding columns, native controls and clear guidance. Never reveal credentials/session values.

The user-requested visual alignment adds locally bundled DM Sans (OFL), Georgia/system serif display headings and unchanged Lucide library icons (ISC), all served from the same origin. `web/views.js` owns the independent presentation, imported as a native browser module by `web/app.js`; no frontend build service is required. A selected-finding/filter view replaces repeated full report forms. Keyboard selection, mobile drawer/Escape and focus restoration are browser-checked. See docs/ui-refresh.md and bundled resource licenses.

## Components
The latest target is conversation-first processing; [the current plan](../docs/conversation-first-plan.md) supersedes the earlier manual workflow as product direction. It does not claim automatic segmentation/deletion or document rebuilding is implemented.

### Shared contracts and routing
Pydantic evidence/finding/citation envelopes; explicit project → approved mapping → unassigned. Unclear passages are left alone, outside project analysis and memory, without a forced question or automatic matching retry. Later routing requires an authorized explicit choice. Source/container/item IDs deduplicate identical deliveries; revisions retain originals. Confirmed segments retain parent provenance. PRD refs: Evidence and routing, Identity and source access.
### Identity and workflow
PBKDF2 passwords, opaque expiring cookie sessions, same-origin mutation guards, workspace/project/source permissions. Review owners assign/dismiss; assignees respond; project owners/decision_owners confirm immutable decision versions. PRD ref: Assignment and resolution.
### Review and providers
Environment-configured OpenAI-compatible Muse Wonder/Groq/NVIDIA interface, bounded inputs, shared schemas, exact quotes and scope/version guard. No guessed primary endpoint or automatic fixture fallback. SQLite project decisions are the shared memory. Source changes invalidate snapshots. PRD ref: Goal-specific findings.
### Source adapters
Manual parsing, Vexa REST, Slack OAuth/selected pulls and Baileys event/manual-import boundary. Explicit network consent; bounded timeouts, redacted failures and retry information. No live claim from contract tests. PRD ref: Sources.

## Data Model
Fresh SQLite `records(kind,id,workspace_id,body_json)` entities: user, session, project, source, source_event, evidence, mapping, review, decision, oauth_state. A process lock and transaction serialize commands. Preserve raw events, immutable evidence revisions and append-only confirmed decisions; keep routing distinct. No source-specific memory engines.

## File Structure
`app/{contracts,storage,service,providers,adapters,api}.py`, `web/`, `tests/`, `samples/`, `docs/`, `devpost/`.

`scripts/launcher.py` provides local dependency/configuration/port checks, safe `.env` creation, browser readiness and repeat-launch reuse. `start.bat` selects supported Python and delegates to it; `scripts/serve.py` starts the local app without access logs. `start.bat --check` performs setup checks without starting a server or contacting external providers. Tests use `create_app(load_settings=False)` to avoid loading real keys.

## External Services and Dependencies
Vexa POST /bots and GET /transcripts/{platform}/{native_meeting_id}, X-API-Key. Slack oauth.v2.access, conversations.info/history/replies and chat.getPermalink with conversation read/history scopes, no send scopes. Baileys unofficial MIT prerelease requires isolated handling; no live pairing until verified. Models use environment URLs/models/keys. See docs/integration-research.md for current primary sources and drift. Keys never enter prompts/logs/source control.

## Important Failure Modes
Unauthorized/ambiguous routing denies or holds evidence; incomplete transcript/parse/connection failures stay visible; provider failures have no fabricated result; edits/deletions invalidate report/confirmation/export; unavailable Baileys uses test/manual import only.

## What Was Simplified and Why
One local process/SQLite and native browser UI reduce Windows setup. Slack uses explicit bounded pulls with visible incomplete coverage rather than unattended subscriptions. Core memory is a deterministic versioned decision record; a future semantic index must obey the same access/routing boundary.

## Decisions and Open Issues
Current direction replaces earlier connector/team deferrals. Source authorization outranks similarity. Live-model verification (fictional documents) passed October 24, 2026 for Muse Wonder and Groq independently and for the controlled-failure fallback via NVIDIA; NVIDIA as an isolated primary exceeded the bounded 35s timeout and is treated as fallback-only within current bounds. One bounded transient-quota retry per provider (Retry-After honored up to 60s) is implemented with a regression test. Real-account tests (Vexa meeting, Slack workspace, WhatsApp pairing) remain separately required and blocked on user-supplied local configuration. No personal learning uncertainty has been reported; tests demonstrate the permission/routing boundary. Local updates only.
