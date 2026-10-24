# Verification — fresh ContextGuard implementation

Recorded October 24, 2026. Results apply to this local rebuild, not to every possible input or to real external account access.

## Executed checks

Latest setup/launcher follow-up: **49 tests passed**, including six added launcher/configuration cases; one nonfailing Starlette TestClient deprecation warning. The updated real Windows launcher starts successfully, a second launch reuses the running instance, and `start.bat --check` reports configuration without provider calls or secret values. The original 43-test/browser evidence below remains the initial build record.

| Check | Observed result |
|---|---|
| New-repository Python environment | Created `.venv` with Python 3.11; installed pinned runtime/test requirements offline from 27 matching third-party wheels recovered from the existing pip HTTP cache |
| Dependency consistency | `.venv/Scripts/python.exe -m pip check`: no broken requirements |
| Regression/API/adapter suite | **43 passed** in the new environment after all code-review repairs and final strict-consent/citation-role changes; one nonfailing Starlette TestClient deprecation warning |
| Windows launcher | Ran actual `cmd.exe /d /c start.bat` using the new `.venv`; served the new app on port 8027 |
| Real Edge browser journey | Seven grouped checks passed, no page errors, using a separate fictional test database |
| Browser output inspection | Downloaded Markdown report inspected; desktop and 390px screenshots inspected |
| JavaScript syntax | `node --check web/app.js` passed |
| Windows DPAPI | Actual synthetic credential protection attempt failed in this execution environment; the app refused plaintext token persistence |
| Slack OAuth + pull pipeline | Controlled HTTP plus an explicitly controlled credential protector; state/replay/scopes/selected channel/provenance/disconnect tested, not a real Slack installation |
| Vexa fetch pipeline | Controlled HTTP through source → common evidence → routed records, revision and original-transcript access |
| Baileys | Selected-chat test/import filtering tested; no library runtime, session pairing or sending capability included |

The first test invocation hit an inaccessible Windows temp directory; `scripts/test.py` now uses a unique ignored artifact-local temp directory. An attempted uv cache installation was denied; an initial offline pip resolution had an incompatible cached wheel tag. Selecting the actual compatible tag produced a successful clean install. This is a cached clean installation, not an online registry installation test.

## Browser checks

1. Fresh owner-account setup and authenticated UI.
2. Three fictional documents → six explicitly labeled deterministic fixture findings.
3. Context answer choices, Other textbox, response and separate authorized confirmation.
4. Stored Markdown report download.
5. Confirmed decision/report persists across reload.
6. Manual unknown note → Unknown Context → explicit project route.
7. 390px layout without horizontal overflow.

Artifacts (ignored): `artifacts/browser/results.json`, `report-desktop.png`, `mobile.png`, `context-gap-report.md`, `app-map.png`. The final browser test used isolated `artifacts/final-browser-acceptance/database.sqlite3`; the normal database was not used. The app map was also checked offline with JavaScript disabled. The browser harness uses an installed third-party Playwright package from the earlier development environment; it imports no earlier application code.

## Code review findings repaired and regression-tested

- A source grant cannot read/revise a previous item routed to a project the caller cannot access.
- Shorter successful document replacement retires removed passages; original text/history remains.
- Source edit/delete or a stale segment ancestor blocks later analysis/confirmation/export from treating old text as current.
- Response citations use the same nonempty exact-quote contract as model citations.
- String values such as `"false"` cannot act as consent or a known answer.
- A complete Slack channel pull does not invalidate replies imported from a specifically selected thread.
- Different explicit scope/version/period/milestone metadata downgrades a proposed contradiction to clarification.
- A response marked unknown stays open; only the appropriate decision owner confirms a resolution.

## Not verified / not implemented as live

Model settings were initially absent. In a subsequent user-authorized setup pass, existing model keys/settings were migrated privately to the new ignored `.env`; no live Muse Wonder/Groq/NVIDIA call was made. No real meeting was joined, Slack workspace installed/pulled or WhatsApp account linked. No live connector earns an integrated/verified label. No deployment, publication, external notifications or message sending was performed. Real external inference accuracy, real source edit/delete behavior and a DPAPI-protected OAuth round trip remain unverified.

Baileys pairing stays disabled rather than claiming supported production operation. Slack is explicit bounded polling, not a live Events subscription; some missing messages may reflect retention/permissions rather than deletion. Document parsers are bounded by file/page/text limits but are not isolated in a separate process. Local accounts are functional but there is no enterprise identity, password reset or retention-management UI. This is a single-process local proof of concept.

## Highest-priority next work

1. Use the locally configured Muse Wonder settings to explicitly run a fictional live review and inspect relevance/quotes/alternate interpretations and the report. Verify endpoint/account and fallback access separately.
2. Validate Windows protected credential storage in the intended user's normal session, then test a real authorized Slack OAuth/channel/thread path or a Vexa meeting through to a live report.
3. Have the learner try the fresh app, resolve actual feedback and explicitly confirm readiness. The Skill Pack's final hands-on checkpoint remains open; an agent-only test is not substituted for it.
