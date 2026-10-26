# Visible processing status

Project Reviews displays processing status directly above the upload/context cards. Status appears immediately when a document upload starts, before the server returns an intake ID, then follows the real server job through queued, project matching, analysis, completion or failure.

## Behavior

- Uploading/preparing has an indeterminate indicator and elapsed time. No percentage is invented.
- Matching shows actual checked/total passages for project relevance, not completed analysis.
- Analysis has a separate batch counter when the server supplies totals; otherwise it stays indeterminate. Full passage matching never labels a review complete.
- The submit button reads Processing and is disabled while the project's current job runs. Programmatic duplicate submissions are rejected too.
- Active jobs restore after reload. Polling updates status; the elapsed clock updates each second. Temporary status-fetch failure shows reconnecting.
- New attempts have a fresh persisted start time; retries no longer count idle time since the original upload. Legacy timing is labelled Since original upload until a new attempt is recorded.
- Local outbound-network failures include normal-user startup guidance. The launcher refuses to start the app under CodexSandboxOffline; see windows-network-recovery.md.
- Completed jobs expose Open review. Failed jobs expose Retry retained input, without a completed-review link even if an intermediate review ID exists.
- Upload rejection remains above the form and keeps the selected file for correction/resubmission.
- Older jobs are in expandable Earlier processing; project selection scopes the displayed jobs.

## Verification

Six Node checks cover upload state, stage/counter semantics, project boundaries, failed partial results, retry timing and network-recovery guidance. Four grouped Edge browser checks use all six actual Synora Markdown files through real local upload/API/SQLite routes with deliberately delayed fictional providers. They verify immediate status, duplicate prevention, active reload, stage transitions, mobile layout, stored-result navigation, retry and upload rejection. All 12 existing grouped browser journeys also pass with zero browser errors.

Start a fresh isolated server (not the normal user database):

```powershell
node --test tests/processing-ui.test.mjs
.\.venv\Scripts\python.exe scripts/browser_server.py --port 8046 --progress-fixture
```

In another terminal:

```powershell
$env:CONTEXTGUARD_URL='http://127.0.0.1:8046'
node scripts/browser-progress.mjs
```

Screenshots/results are under ignored artifacts/processing-ui/. These checks verify progress behavior, not live model quality. A read-only audit found the user's larger upload included README/transcript, and an earlier six-document run failed citation validation; the latest retry failed before routing because local Windows/network permissions blocked every provider. This UI update does not claim that live review passed. Existing uncommitted batching/provider work is preserved separately.

## Try it

Refresh the local app, select the test project, upload only samples 01 through 06 and process with the intended consent. Status appears immediately above Add context. Analyzing findings remains visible after matching reaches its total. Completion provides Open review; failure explains the error and offers retry. Static UI changes need a browser refresh and no frontend build. Backend intake/launcher changes require a restart: start the app under the normal Windows account, then retry retained input. See [Windows recovery](windows-network-recovery.md).
