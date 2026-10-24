# ContextGuard

A local goal-based context and decision-readiness checker. Select project sources, inspect conflicts/gaps beside exact passages, ask the accountable person, and retain a confirmed decision history. This is a fresh implementation following the Devpost Learn planning/build structure and the user's current written product brief.

## Run on Windows

Python 3.11+ is required. Double-click `start.bat`, or run it in PowerShell. First setup creates `.venv` and installs pinned dependencies from `requirements.txt`; that installation requires package access. A broken environment is preserved with repair instructions. No frontend build or Node service is required for the app.

Open **http://127.0.0.1:8027**. Create the first local owner account with a password of at least 10 characters. Keep the terminal open; Ctrl+C stops the app. This is a different port/database from the earlier ContextGuard project.

The launcher checks Python 3.11+, pinned dependencies and port 8027, creates a secret-free `.env` only when missing, prints connection readiness without key values, and opens the browser after the server is ready. Launching it again reuses this same running workspace. An occupied port is reported without stopping any process. `start.bat --check` shows setup status without starting the app. Set `CONTEXTGUARD_NO_BROWSER=1` to skip opening the browser, or `CONTEXTGUARD_NO_PAUSE=1` for noninteractive error handling. Available artifact-local package wheels are tried before online installation. See [current setup status](docs/setup-status.md).

Manual commands:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts\serve.py
```

If you explicitly want an already prepared Python environment, set `CONTEXTGUARD_PYTHON` to its Python executable before running the launcher. It must contain the declared dependencies. This is optional and never copies application code.

## Try the fictional demo

1. Create/sign into your local account.
2. Click **Try fictional three-document sample**. It creates an Orchid project and three labeled fictional manual sources.
3. Enter a goal such as “Can the v2 pilot proceed?” Check **Use fictional test analysis**, then run the review. Six deterministic fixture findings demonstrate conflict, missing information, assumption, dependency, old version and ambiguity cases. This is not a live model or measured detection-accuracy demonstration.
4. Inspect source passages, choose an accountable project member, record a context-based answer or Other, then confirm as a project owner/decision owner. A response marked unknown remains open.
5. Reload to see persistence; download the report. In Sources, import a note without a project to try the Unknown Context inbox. Confirm a route before it can enter a project review.

Three self-authored documents live under `samples/`. The public-launch date is a negative control: it must not be confused with the pilot milestone.

## Team and source access

Workspace owners create local accounts. Project owners grant project roles in Team and optionally configure responsibility topics. Sources have their own access lists. Review creators manage assignments/dismissals; accountable assignees respond; only a project owner or decision_owner confirms. One assignee may have collaborators/watchers. Entering a name or assigning a finding does not send a message.

Project identity order: explicit project → approved source mapping → Unknown Context. Local name hints and explicit model suggestions remain suggestions. Unknown evidence cannot read/write decision memory. Confirmed exact segments retain the full original source and provenance. Earlier decisions are immutable versions with actors/timestamps/citations and supersession links.

## Models

The launcher creates **this project's** `.env` from `.env.example` if absent. Configure keys privately; the application never loads another project's `.env`. During the user's authorized local setup, existing supported model keys/settings were migrated into the ignored new `.env`, including the Muse model/endpoint used by the earlier app. No database, source content or connector session was copied, and no live call was made. Muse Wonder is primary via `MODEL_BASE_URL`, `MODEL_NAME`, `MODEL_API_KEY`. For a new installation, enter the actual provider-supplied OpenAI-compatible base URL and model ID. Groq uses `GROQ_API_KEY` / `GROQ_MODEL` (default `openai/gpt-oss-120b`); NVIDIA uses `NVIDIA_API_KEY` / `NVIDIA_MODEL`. Keys are never displayed or committed.

Live analysis requires the explicit external-transfer checkbox. Selected evidence and visible prior decisions may be sent through the configured fallback chain. Schema/citation checks reject invalid findings; failure never silently substitutes fictional results. The model settings are locally present; no live model has been verified in this fresh repository.

## Source connection setup and actual status

| Source | Current implementation | What remains unverified |
|---|---|---|
| Manual | Pasted text, TXT/MD/PDF/DOCX; filenames/pages/paragraphs, size bounds and visible failures | Broader document corpus and production parser isolation |
| Vexa | Explicit join/stop/fetch REST client, speaker/time/partial handling, controlled HTTP pipeline tests | Authorized real meeting admission/transcript → report run |
| Slack | OAuth/state/expiry, protected-token interface, selected channel/thread/date pulls, links, bounded pagination and revocation/rate-limit errors | Real workspace installation/pulls, token scope behavior and Windows credential-store round trip |
| WhatsApp/Baileys | Selected-chat Baileys-shaped test-event import and manual TXT fallback | Live pairing/runtime is disabled; no connected WhatsApp integration is claimed |

**Vexa:** configure `VEXA_BASE_URL` and `VEXA_API_KEY`. Register `platform:native_meeting_id` (e.g. `google_meet:abc-defg-hij`; `teams` and `zoom` use numeric native IDs). Select Join and explicitly confirm authorization/participant consent. Fetch is separate; a host may need to admit the bot. Hosted Vexa is external; self-hosting requires Vexa's additional services/Docker, including STT configured at its boundary. ContextGuard does not contain Whisper or an audio transcription pipeline. Recording is disabled in the join request.

**Slack:** configure `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET` and a redirect URI approved in your Slack app (default `http://127.0.0.1:8027/api/slack/callback`; use an explicitly configured callback approach permitted by Slack). Settings opens official OAuth with public-channel read/history scopes only. Private channels require separately approved `groups:read`/`groups:history`. Register a selected `TEAM_ID:CHANNEL_ID` source and supply a specific thread/date range if needed. An explicit locally configured token plus `SLACK_TEAM_ID` is an alternative. OAuth tokens use Windows-current-user DPAPI; this execution environment denied DPAPI, so real persistence fails safely. No plaintext fallback is written. Access logs are disabled. Local disconnect disables local access; revoke the app in Slack to invalidate its external token.

Slack is explicitly pulled, not an Events API subscription. Edits/deletions observed in returned payloads create revisions/tombstones. Missing items in complete selected pulls are marked uncertain/unavailable, not proven deleted. Thread-only replies are not retired by channel history. Truncated pulls remain partial. There is no claim of complete Slack workspace coverage.

**Baileys:** inspected upstream MIT license/docs and current prerelease before implementation. It is unofficial; authorized supported live operation has not been verified, so no library runtime, QR pairing, full-history synchronization or send endpoint is included. Register one selected chat ID and use manual export or fictional event import. Unselected chat events are discarded before persistence. See [integration research](docs/integration-research.md) before considering a future isolated bridge.

## Tests and verification

```powershell
.venv\Scripts\python.exe scripts\test.py
```

The test runner uses a new ignored artifact-local temp folder, never the normal database. Browser verification uses Playwright and installed Microsoft Edge; install `@playwright/test` in your development tools and set `CONTEXTGUARD_PLAYWRIGHT_PACKAGE` to that tools directory's `package.json`, then run `node scripts/browser-check.mjs` against a fresh isolated test database at 8027. This is a development tool, not an app runtime dependency. The runner creates fictional users/reviews, screenshots and a downloaded report under ignored `artifacts/`.

Current evidence and limitations are recorded in [verification](docs/verification.md). Exact citation matching establishes provenance, not truth or exhaustive semantic accuracy. Visible Ready/Ready with actions/Needs clarification rules are in the report; no numerical readiness score is used.

## Design, privacy and planning

- [Architecture and data flow](docs/architecture.md)
- [Privacy and service boundaries](docs/privacy.md)
- [Implementation audit](docs/implementation-audit.md)
- [Scope](devpost/scope.md), [PRD](devpost/prd.md), [spec](devpost/spec.md), [build checklist](devpost/checklist.md)
- [Offline implementation map](devpost/app-map.html)

The app binds only to localhost. Protect your Windows account/disk: local evidence records are not encrypted at rest. There is no production retention UI or enterprise identity. Do not expose it publicly. Credentials, databases, artifacts and the private learner profile are ignored. No deployment/publication/source connection happens automatically.

## Provenance and curriculum

The earlier [ContextGurd](https://github.com/Ratnadeep-2007/ContextGurd) idea/design exploration is disclosed pre-existing work. No earlier application code, database schema, prompts, tests or generated planning documents were copied. Synora is only a high-level conceptual reference, not this product or its implementation. Standard third-party libraries and development tools are reused normally. See THIRD_PARTY_NOTICES.md.

The official [Devpost Learn Skill Pack](https://github.com/challengepost/learn-ai-basics) is installed locally under ignored `.agents/skills/`. Onboarding facts and the current user-written product direction informed fresh planning; no complete historical interview or final learner review is fabricated. Creating a new repo does not itself establish hackathon eligibility.

## GitHub branch

At the user's request, this fresh implementation is published as a snapshot on [`contextguard-learn-rebuild`](https://github.com/Ratnadeep-2007/ContextGurd/tree/contextguard-learn-rebuild) in the existing ContextGurd repository. The existing `main` application is preserved. This branch's root contains the fresh app; it is not the earlier app plus a nested copy. Private `.env`, learner profile, database, dependencies and artifacts are excluded. The local repository retains its independent build commits; the GitHub snapshot has a different commit identity. See [build history](docs/build-history.md).

```powershell
git clone --branch contextguard-learn-rebuild --single-branch https://github.com/Ratnadeep-2007/ContextGurd.git ContextGuard-Learn
cd ContextGuard-Learn
.\start.bat
```

Cloning excludes private keys; configure the new clone's `.env` locally. The working machine's existing ignored key file is never published.
