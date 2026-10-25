# Verification — fresh ContextGuard implementation

Recorded October 24, 2026. Results apply to this local rebuild, not to every possible input or to real external account access.

## Executed checks

October 25 status inspection: **57 tests passed** after the scoped Vexa key support was added. The local app responds 200; Vexa bot status responds 200 and an unknown meeting transcript read responds 404. Muse/Groq and NVIDIA fallback results were inspected from existing real-run artifacts rather than rerun. No real Vexa meeting transcript exists yet. See docs/latest-status.md for the current completion matrix; earlier statements about missing Vexa keys below are historical.

Latest live follow-up (October 24, 2026, normal user session): **56 automated tests passed** and **nine grouped browser checks passed** on an isolated instance/database. `start.bat --live-check` now verifies Muse Wonder and Groq independently and the controlled-primary-failure → real-fallback path (via NVIDIA), all with fictional documents and human semantic review of findings/citations. NVIDIA as isolated primary exceeded the bounded 35s timeout (raw probe ≈80s, truncated output) and is not certified as a primary. One bounded transient-quota retry per provider was added with a regression test. A synthetic DPAPI protect/decrypt round trip succeeded in this normal session; the earlier denial was the sandboxed agent user. See docs/live-testing.md for the full record.

Previous live-verification tooling follow-up: **55 automated tests passed** (one nonfailing Starlette TestClient deprecation warning). New checks cover secret-safe Windows/HTTP diagnostics, individual-provider key isolation/restoration, source consent gating, controlled failover setup and explicit launcher live-test dispatch. At that time `start.bat --live-check` could not verify providers because the sandboxed session denied outbound connections; no live pass was inferred from the automated suite.

Latest setup/launcher follow-up: **49 tests passed**, including six added launcher/configuration cases; one nonfailing Starlette TestClient deprecation warning. The updated real Windows launcher starts successfully, a second launch reuses the running instance, and `start.bat --check` reports configuration without provider calls or secret values. The original 43-test/browser evidence below remains the initial build record.

Latest UI follow-up: **nine grouped browser checks passed**, including selected-finding keyboard navigation, recorded/all filters, mobile drawer/Escape/focus restoration, Other/response/confirmation, export, reload and Unknown Context routing. No page errors. Reference/before/after captures and the visual comparison are documented in docs/ui-refresh.md. The 49-test backend/launcher record is separate; this visual change did not alter the backend.

The user also explicitly requested real provider checks. In the earlier sandboxed session, Muse Wonder, Groq and NVIDIA were each attempted independently with self-authored fictional passages and **all failed before an HTTP response (`errno 13`, `winerror 10013`)**. Re-run in a normal user session (see the latest follow-up above), Muse Wonder and Groq verify independently, the controlled-failure fallback verifies via NVIDIA, and only NVIDIA-as-primary remains uncertified (latency/output-length within current bounds). Vexa/Slack keys/accounts are absent; Baileys pairing remains disabled, so no real source account was contacted.

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

Model settings were initially absent. In a subsequent user-authorized setup pass, existing model keys/settings were migrated privately to the new ignored `.env`. Fictional live provider verification has since passed for Muse Wonder and Groq, plus the controlled-failure fallback via NVIDIA, as recorded above; broader real-world inference accuracy beyond the fictional bundles is not established. No real meeting was joined, Slack workspace installed/pulled or WhatsApp account linked. No live connector earns an integrated/verified label. Real source edit/delete behavior and a DPAPI-protected round trip with a real OAuth token (synthetic DPAPI round trip passed) remain unverified. Branch publication was separately authorized later; this verification record does not imply deployment, external notifications or message sending.

Baileys pairing stays disabled rather than claiming supported production operation. Slack is explicit bounded polling, not a live Events subscription; some missing messages may reflect retention/permissions rather than deletion. Document parsers are bounded by file/page/text limits but are not isolated in a separate process. Local accounts are functional but there is no enterprise identity, password reset or retention-management UI. This is a single-process local proof of concept.

## Highest-priority next work

1. ~~Use the locally configured Muse Wonder settings to explicitly run a fictional live review and inspect relevance/quotes/alternate interpretations and the report. Verify endpoint/account and fallback access separately.~~ Done October 24, 2026 (Muse + Groq verified, fallback verified via NVIDIA; NVIDIA-as-primary remains latency-bound). Re-run after material prompt/provider changes.
2. Test a real authorized Slack OAuth/channel/thread path or a Vexa meeting through to a live report. Blocked on user-supplied local configuration: `VEXA_API_KEY` + authorized test meeting (`VEXA_TEST_PLATFORM`, `VEXA_TEST_MEETING_ID`), or Slack OAuth app settings (`SLACK_CLIENT_ID`/`SLACK_CLIENT_SECRET`) / scoped token + `SLACK_TEAM_ID` + selected `SLACK_TEST_CHANNEL_ID`. Synthetic DPAPI protection already passes in the normal session.
3. Have the learner try the fresh app, resolve actual feedback and explicitly confirm readiness. The Skill Pack's final hands-on checkpoint remains open; an agent-only test is not substituted for it.
