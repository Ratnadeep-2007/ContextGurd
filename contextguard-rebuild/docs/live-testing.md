# Real model and source verification

## Current observed result

Updated October 24, 2026 after re-running in a normal Windows user session. An explicitly authorized live check used the three self-authored fictional documents through the real shared ingestion, routing, goal-analysis and report pipeline in isolated artifact databases.

**Network diagnosis:** the earlier `winerror 10013` denial occurred in a restricted sandboxed agent session. In the normal user session, direct connections succeed (no proxy is configured: WinHTTP direct, no proxy environment variables; provider calls use `httpx` with `trust_env=False`). No security control was disabled or bypassed.

**Observed live results (fictional documents, human-reviewed):**
- **Muse Wonder: verified.** Complete analysis, 7 findings, schema/citations/report verified. Human review: the January 18 vs 25 same-pilot disagreement was the only potential conflict; March 12 public launch was correctly *not* flagged (different milestone, recorded as verified fact); v1 exporter correctly downgraded to clarification; approval, credentials, free-service assumption and missing performance target all found with exact quotes.
- **Groq: verified independently** (multiple clean runs, 5–6 correct findings, no false conflict). Intermittency observed and diagnosed: one candidate finding was correctly rejected by the citation verifier; several attempts were rejected by Groq's token quota (observed limit 8,000 tokens/minute; one analysis consumes ≈4,300 tokens; gateway answered 413/429). The provider layer now retries one transient 413/429/5xx response per provider, honoring `Retry-After` up to a bounded 60s (`app/providers.py`), with a regression test.
- **NVIDIA: verified as a real fallback responder** (complete, 6 semantically sound findings, report verified). As an isolated primary it twice exceeded the bounded 35s client timeout (one raw probe answered HTTP 200 in ≈80s with output truncated at the token cap; a JSON-object-mode probe exceeded 240s). It is therefore not certified as a primary within current bounds; the timeout was not inflated to chase it.
- **Controlled primary failure → real fallback: verified.** With the primary transport failed locally by design, the chain reached real fallback providers and produced a verified NVIDIA report (`artifacts/live-checks/f5dac2d52dd24929bc6345a7abcd1515/`). The verifier paces this scenario by 65s to respect the observed Groq quota window. This is a controlled-failure scenario, not a naturally observed outage.

Results are under ignored `artifacts/live-checks/` (per-run `results.json`, reports, `verification.sqlite3`). Nothing was written into normal project memory, and no real source account was contacted.

## Repeat the model checks

From this repository in a normal Windows terminal:

```powershell
.\start.bat --live-check
```

This is an **explicit external-transfer operation**: it sends only the bundled fictional documents to the configured model providers. It creates an isolated verification database and never silently substitutes a fixture. A nonzero exit means verification did not complete; it does not delete reviews or imply installation is broken.

The script checks providers individually, preserving the actual environment values afterwards. Once a real fallback responds successfully, `--fallback` simulates one local primary connection failure and checks the real fallback HTTP path. That is clearly labeled a controlled-primary-failure scenario, not a naturally observed outage. Citation/schema/report success is separate from human assessment of relevance and correctness.

For one provider:

```powershell
.venv\Scripts\python.exe scripts\verify_live.py --live --models muse
```

If the same Windows denial persists, the process/network policy must permit access before live tests can succeed. The agent does not disable security controls or work around restricted network permissions. No key should be pasted into chat or put in a tracked file.

## Vexa: local account configured; selected meeting and full test pending

Configure these **privately** in `.env`: `VEXA_BASE_URL`, `VEXA_TEST_PLATFORM` and `VEXA_TEST_MEETING_ID`, plus Vexa key(s). Vexa keys are **scoped** (dashboard "Create API Key"): a Bot Key (`vxa_bot_`, scope `bot`) sends/stops bots, and a Transcription Key (`vxa_tx_`, scope `tx`) reads transcripts/meetings. This app accepts either one combined key in `VEXA_API_KEY` **only if it carries both scopes**, or the pair `VEXA_BOT_KEY` + `VEXA_TX_KEY` (added October 24, 2026 after the dashboard split was identified; per-scope header use is regression-tested). Optional meeting passcode: `VEXA_TEST_PASSCODE`. Use a fictional test meeting you are authorized to process and inform participants as appropriate. An API key alone is not authorization to join any meeting.

The ordinary app offers explicit Join/Stop/Fetch controls. The verification script never joins automatically. Fetching an existing selected transcript is available through the source command below; an explicit bot request additionally needs `--join-vexa --participants-informed`. A transcript may not yet exist immediately after admission; rerun Fetch rather than inventing text. No duplicate STT pipeline is added.

**Local wiring completed October 25, 2026:** a pre-existing self-hosted Vexa v012 stack on this machine (gateway `127.0.0.1:18056`, admin `127.0.0.1:18057`) was reused; nothing was installed or paid for. A dedicated `contextguard@local` Vexa user and a `bot`+`tx` scoped key were minted via the local admin API and stored only in ContextGuard's ignored `.env` (`VEXA_BASE_URL=http://127.0.0.1:18056`; same combined-scope key also fills `VEXA_BOT_KEY`/`VEXA_TX_KEY`). Validation: `GET /bots/status` → 200 (bot scope), `GET /transcripts/google_meet/abc-defg-hij` → 404 (tx scope authorized, unknown meeting), and the app-code fetch path produced the expected real-request failure for that nonexistent meeting instead of a configuration error. Deployment transcription is configured to the local CPU Whisper service (`host.docker.internal:8083`, worker healthy), so meeting audio need not leave this machine. Still outstanding: one real fictional meeting (join → admission → speech → stop → fetch → routed report) with the user present.

## Slack: missing app authorization and selected channel/thread

Configure an OAuth app in the app's Settings and authorize the workspace, or explicitly configure a minimum-scoped local `SLACK_BOT_TOKEN` plus `SLACK_TEAM_ID` for the CLI check. Select a fictional test channel via `SLACK_TEST_CHANNEL_ID`, optionally `SLACK_TEST_THREAD_TS`. Public channel read/history scopes are sufficient for that initial path; private channel scopes should be added only for a selected authorized private channel.

The CLI does not extract protected OAuth tokens from another account or database. Actual OAuth/browser acceptance is distinct from a local-token ingestion check. Windows DPAPI protection was denied in the earlier sandboxed session; a synthetic protect/decrypt round trip later passed in the normal user session. A real Slack OAuth token round trip, token scopes, workspace access, channel membership and source coverage remain unverified. The app refuses plaintext OAuth persistence if protection fails.

## Explicit selected-source ingestion check

After configuring selected fictional Vexa/Slack sources:

```powershell
.venv\Scripts\python.exe scripts\verify_live.py --sources --source-consent --project "Authorized fictional source test"
```

This tests actual selected source → adapter → shared evidence → explicit project routing in a dedicated local verification workspace. It preserves provenance and parsing status. It does **not** send real source text to a model automatically or claim final end-to-end browser/report certification. Use the ordinary app with explicit model transfer consent for that final check. The project name/selection and consent flags are required before any real source read. Missing configuration produces a named blocker, not a mock replacement.

## WhatsApp/Baileys: still not connected

The live pairing/runtime is not implemented or verified in this build. Current upstream [package metadata](https://github.com/WhiskeySockets/Baileys/blob/master/package.json) (rechecked October 24, 2026) still describes version `7.0.0-rc14` — a moving prerelease, MIT licensed, Node ≥20 — not a stable release to pin; inspect the [upstream guide](https://github.com/WhiskeySockets/Baileys/blob/master/.github/README.md) and the existing integration research before adding it. An installed Node executable or a manually imported event is not a connected WhatsApp account.

A synthetic Windows DPAPI protect/decrypt round trip now passes in a normal user session (the earlier failure was the sandboxed agent user), so protected storage is no longer the blocker it was. Remaining blockers: no stable pinned Baileys release (RC only), no tested encrypted design for Baileys' multi-file session state, no user-selected account/chat or QR scan supplied, and unofficial-service authorization risk that must be the user's informed choice. Safe live work therefore still needs a tested pinned runtime, encrypted/OS-protected session handling, source allowlisting before retention, explicit connect/disconnect controls and the user's pairing interaction. Do not enable raw session files, whole-chat scraping, message logging, sending or automatic replies just to make a status turn green. Manual selected-chat export and labeled test-event import remain available.

## What is needed from the user

Provide configuration locally and identify the authorized Vexa test meeting and Slack channel/thread. Keep keys/passcodes in `.env`, not chat. WhatsApp requires a selected chat/group and user-controlled pairing when a safely tested live flow is available. Until these inputs and environment access exist, the real-integration checklist remains incomplete.
