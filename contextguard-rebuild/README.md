# ContextGuard

A local conversation-first context and decision-readiness checker. Upload or capture authorized context, generate project-specific cited reviews, clarify findings, retain confirmed decisions and export a report or consolidated Word document. This is a fresh implementation following the Devpost Learn planning/build structure and the user's current written product brief.

## Run on Windows

Python 3.11+ is required. Double-click `start.bat`, or run it in PowerShell. First setup creates `.venv` and installs pinned dependencies from `requirements.txt`; that installation requires package access. A broken environment is preserved with repair instructions. No frontend build or Node service is required for the app.

Open the URL printed by the launcher (preferred **http://127.0.0.1:8027**; **http://127.0.0.1:8028** on this machine while the older instance is preserved). Create the first local owner account with a password of at least 10 characters. Keep the terminal open; Ctrl+C stops the app. This is a different port/database from the earlier ContextGuard project.

The launcher checks Python 3.11+, pinned dependencies and port 8027, creates a secret-free `.env` only when missing, prints connection readiness without key values, and opens the browser after the server is ready. Launching it again reuses the updated running workspace. If an older rebuild occupies the preferred port, it is preserved and the updated app is opened on an available port from 8028 to 8035. Unrelated occupied ports are reported without stopping processes. `start.bat --check` shows setup status without starting the app. Set `CONTEXTGUARD_NO_BROWSER=1` to skip opening the browser, or `CONTEXTGUARD_NO_PAUSE=1` for noninteractive error handling. Available artifact-local package wheels are tried before online installation. See [current setup status](docs/setup-status.md).

`start.bat --live-check` explicitly tests real models/fallback access using only the bundled fictional documents and saves redacted local evidence. This contacts external providers; it is separate from ordinary startup/`--check`. Earlier sandboxed attempts were blocked by Windows; later normal-session runs verified Muse Wonder and Groq independently and a controlled-primary-failure path through real NVIDIA fallback. NVIDIA as an isolated primary remains latency-bound. See [real testing and account requirements](docs/live-testing.md). Experimental Baileys pairing is implemented; runtime installation, Windows session protection and an actual phone scan still require live verification. See [WhatsApp setup](docs/whatsapp-live.md).

Manual commands:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts\serve.py
```

If you explicitly want an already prepared Python environment, set `CONTEXTGUARD_PYTHON` to its Python executable before running the launcher. It must contain the declared dependencies. This is optional and never copies application code.

## Try the current workflow

1. Sign in, create a project above the cards in Project Reviews and describe its work and default review goal.
2. In **Project Reviews**, upload documents or paste a conversation. Source records are created automatically. Select Current project to scope document/text processing, confirm authorization/model consent, then click **Process content**.
3. Watch processing status. Complete input is covered in validated batches; matched project passages generate separate reviews. Unmatched content is removed from active input after all analyses succeed. Failed processing retains the input for explicit retry.
4. Filter the review library by project, source, creation date and status. Open findings beside their exact evidence; assign, answer and separately confirm as an authorized decision owner.
5. Download the report or the updated Word document. Confirmed answers become versioned project decisions. Original files are not overwritten.

**Try fictional sample** reopens an existing demo instead of creating duplicates. This machine keeps one Synora project with three fictional documents and six assigned findings. A fresh workspace can still create its first bundled sample without model calls. Six deterministic findings demonstrate a conflict, missing approval, cost assumption, dependency, earlier version and ambiguous performance target. It is a workflow demonstration, not a live AI accuracy claim. The public-launch date is a different milestone and should not be confused with the pilot.

See [the complete workflow and current limits](docs/conversation-workflow.md). **Sources** contains connection checks, Slack OAuth and explicit Vexa meeting-link Join/Stop/Fetch controls. Uploads, conversation inspection and review filters belong in Project Reviews. There is no source-registration panel or Unknown Context tab.

## Team and source access

This demo keeps Ratnadeep as admin and shows four existing fictional members with roles/responsibilities in the minimal Team table. Account/role APIs remain available for compatibility; account-creation forms are not shown. Sources have their own access lists. Review creators manage assignments/dismissals; accountable assignees respond; only a project owner or decision_owner confirms. One assignee may have collaborators/watchers. Entering a name or assigning a finding does not send a message.

Project identity order: explicit project → approved source mapping → Unknown Context. Local name hints and explicit model suggestions remain suggestions. Unknown evidence cannot read/write decision memory. Confirmed exact segments retain the full original source and provenance. Earlier decisions are immutable versions with actors/timestamps/citations and supersession links.

## Models

The launcher creates **this project's** `.env` from `.env.example` if absent. Configure keys privately; the application never loads another project's `.env`. During the user's authorized local setup, existing supported model keys/settings were migrated into the ignored new `.env`, including the Muse model/endpoint used by the earlier app. No database, source content or connector session was copied, and no live call was made. Muse Wonder is primary via `MODEL_BASE_URL`, `MODEL_NAME`, `MODEL_API_KEY`. For a new installation, enter the actual provider-supplied OpenAI-compatible base URL and model ID. Groq uses `GROQ_API_KEY` / `GROQ_MODEL` (default `openai/gpt-oss-120b`); NVIDIA uses `NVIDIA_API_KEY` / `NVIDIA_MODEL`. Keys are never displayed or committed.

Live analysis requires the explicit external-transfer checkbox. Selected evidence and visible prior decisions may be sent through the configured fallback chain. Schema/citation checks reject invalid findings; failure never silently substitutes fictional results. Muse Wonder and Groq have verified live fictional-document reports; NVIDIA has a verified live fallback report, while isolated-primary runs exceeded the current timeout. These limited checks do not establish exhaustive real-world detection accuracy.

## Source connection setup and actual status

| Source | Current implementation | What remains unverified |
|---|---|---|
| Manual | Pasted text, TXT/MD/PDF/DOCX; filenames/pages/paragraphs, size bounds and visible failures | Broader document corpus and production parser isolation |
| Vexa | Local self-hosted gateway configured; dedicated scoped key; separate bot/transcription key support; current bot-status request returns 200 | Actual authorized meeting admission, speech, transcript and final report remain untested |
| Slack | OAuth/state/expiry, protected-token interface, selected channel/thread/date pulls, links, bounded pagination and revocation/rate-limit errors | Real workspace installation/pulls, token scope behavior and Windows credential-store round trip |
| WhatsApp/Baileys | Experimental QR pairing, encrypted local session, explicit chat selection, selected live-text processing and manual TXT fallback | Dependency download and Windows DPAPI were denied in this session; no real account paired |

**Vexa:** this working machine is configured to the local self-hosted gateway at `127.0.0.1:18056` with a dedicated ContextGuard key. For another installation, configure `VEXA_BASE_URL` plus a combined bot/transcription-scoped `VEXA_API_KEY`, or separate `VEXA_BOT_KEY` and `VEXA_TX_KEY`. Paste the supported meeting invitation URL in Sources. Native identifiers are parsed and registered internally. Click Join with explicit authorization/participant consent, then Fetch and process after the meeting; a host may need to admit the bot. The current local deployment uses its own local CPU transcription service at the Vexa boundary; ContextGuard consumes transcripts and contains no duplicate audio/STT pipeline. Recording is disabled in the join request. A 404 for a nonexistent meeting is not a completed transcript test.

**Slack:** configure `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET` and a redirect URI approved in your Slack app (default `http://127.0.0.1:8027/api/slack/callback`; use an explicitly configured callback approach permitted by Slack). Sources opens official OAuth with public-channel read/history scopes only. Private channels require separately approved `groups:read`/`groups:history`. Load authorized public channels and select one in Project Reviews; optionally narrow the thread/date range. The selected source is registered internally. Use the app's active port in your approved callback URI. An explicit locally configured token plus `SLACK_TEAM_ID` is an alternative. OAuth tokens use Windows-current-user DPAPI: a synthetic round trip passed in the normal user session; the earlier sandboxed session denied it. A real Slack OAuth token round trip remains untested. No plaintext fallback is written. Access logs are disabled. Local disconnect disables local access; revoke the app in Slack to invalidate its external token.

Slack is explicitly pulled, not an Events API subscription. Edits/deletions observed in returned payloads create revisions/tombstones. Missing items in complete selected pulls are marked uncertain/unavailable, not proven deleted. Thread-only replies are not retired by channel history. Truncated pulls remain partial. There is no claim of complete Slack workspace coverage.

**Baileys:** experimental read-only pairing is isolated in `connectors/whatsapp` behind the local authenticated API. Run `setup-whatsapp.bat`, then pair and select chats in Sources. Process collected text in Project Reviews. No API key is required; your phone must scan the QR. Full-history sync, media extraction, replies and message-send controls are absent. Session data is AES-GCM encrypted with a Windows DPAPI-protected key; pairing refuses to start if protection fails. No real pairing is claimed: npm download and DPAPI were denied in this execution session. See [setup and limitations](docs/whatsapp-live.md) and [current primary-source research](docs/baileys-research.md).

See [Sources controls and current connection setup](docs/sources-guide.md) before trying a real meeting or Slack workspace.

## Tests and verification

```powershell
.venv\Scripts\python.exe scripts\test.py
```

The test runner uses a new ignored artifact-local temp folder, never the normal database. Browser verification uses Playwright and installed Microsoft Edge; install `@playwright/test` in your development tools and set `CONTEXTGUARD_PLAYWRIGHT_PACKAGE` to that tools directory's `package.json`, then run `node scripts/browser-check.mjs` against a fresh isolated test database (default test URL `http://127.0.0.1:8037`, override with `CONTEXTGUARD_URL`). This is a development tool, not an app runtime dependency. Start the isolated server with `.venv\Scripts\python.exe scripts\browser_server.py --port 8037`, then run the browser check. This server refuses external model calls and creates a fresh ignored database. The runner covers fictional success and controlled failure/retry, saving screenshots and report/Word downloads under ignored `artifacts/`.

Current conversation-first evidence and limitations are recorded in [verification](docs/conversation-verification.md). The new full-pipeline fictional live attempt was blocked by Windows outbound permissions; this does not certify the new matching prompt against real models. Run `scripts/verify_conversation.py --live` explicitly to retry fictional live verification in an environment with provider access. Exact citation matching establishes provenance, not truth or exhaustive semantic accuracy. Visible Ready/Ready with actions/Needs clarification rules are in the report; no numerical readiness score is used.

## Design, privacy and planning

- [UI refresh and original ContextGuard comparison](docs/ui-refresh.md) — fresh presentation code inspired by the outer app, with locally bundled typography/icons, a selectable finding/detail report, filters and mobile navigation.
- [Architecture and data flow](docs/architecture.md)
- [Current conversation-first product direction](docs/conversation-first-plan.md) — target workflow and work still required.
- [Complete flow image](docs/diagrams/contextguard-complete-flow.png) and [editable diagram](docs/diagrams/contextguard-complete-flow.html)
- [Single Synora demo, mock members and walkthrough](docs/test-users.md)
- [Privacy and service boundaries](docs/privacy.md)
- [Implementation audit](docs/implementation-audit.md)
- [Scope](devpost/scope.md), [PRD](devpost/prd.md), [spec](devpost/spec.md), [build checklist](devpost/checklist.md)
- [Offline implementation map](devpost/app-map.html)

The app binds only to localhost. Protect your Windows account/disk: local evidence records are not encrypted at rest. There is no production retention UI or enterprise identity. Do not expose it publicly. Credentials, databases, artifacts and the private learner profile are ignored. No deployment/publication/source connection happens automatically.

## Provenance and curriculum

The earlier [ContextGurd](https://github.com/Ratnadeep-2007/ContextGurd) idea/design exploration is disclosed pre-existing work. No earlier application code, database schema, prompts, tests or generated planning documents were copied. Synora is only a high-level conceptual reference, not this product or its implementation. Standard third-party libraries and development tools are reused normally. See THIRD_PARTY_NOTICES.md.

The official [Devpost Learn Skill Pack](https://github.com/challengepost/learn-ai-basics) is installed locally under ignored `.agents/skills/`. Onboarding facts and the current user-written product direction informed fresh planning; no complete historical interview or final learner review is fabricated. Creating a new repo does not itself establish hackathon eligibility.

## GitHub location

The current rebuild is published under [`contextguard-rebuild/` on main](https://github.com/Ratnadeep-2007/ContextGurd/tree/main/contextguard-rebuild). The earlier root-level application remains preserved. The separate `contextguard-learn-rebuild` branch is an older snapshot; it is not the location of these latest fixes. Local independent commits and GitHub snapshot commit identities differ; see [build history](docs/build-history.md).

```powershell
git clone https://github.com/Ratnadeep-2007/ContextGurd.git
cd ContextGurd\contextguard-rebuild
.\start.bat
```

Configure the new clone's `.env` locally. Private keys, accounts, linked-device sessions, learner profile, database, dependencies and artifacts are excluded. The local test-data reset is not uploaded as a database; fresh clones start without your local accounts or reviews.
