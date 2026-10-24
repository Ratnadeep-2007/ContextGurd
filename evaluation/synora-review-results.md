# Six-file Synora review — observed results

## Actual browser/API run

The six numbered Markdown files in `synora-review-pack/` were uploaded through the running ContextGuard UI on October 24, 2026. The generated local case is **Synora · six-source review test**, ID `6df5d92a348244489097b0b91193afb5`.

- All six sources parsed successfully.
- Extracted passage text matched the original files, and stored SHA-256 hashes matched the uploaded bytes.
- All sources persisted after a browser reload.
- The source dialog displayed extracted passages.
- No browser page errors occurred.
- Live detection could not run: the app had no configured AI provider. The UI disabled analysis, and a direct analysis request returned HTTP 400 rather than fabricated results.

Recorded evidence: `artifacts/synora-review/results.json`, `case-output.json`, and `browser-output.png`. These files are generated artifacts and are not a live model report.

## Reference checks

The intended disagreements are:

| Topic | Source statements requiring clarification |
|---|---|
| Canvas input | Product brief excludes canvas edits; project lead proposal imports saved edits as evidence. |
| Approval | Architecture notes hold replacements of approved requirements for review; the email proposes automatic writes including existing-requirement updates. |
| Timing | Product brief/email propose December 7, 2026; architecture/checklist target January 18, 2027. |

These are synthetic drafts/proposals. A useful review should ask which statement is authoritative, retain that uncertainty, and avoid declaring the whole project blocked.

Manually annotated candidate findings for those three topics were supplied to the actual deterministic verifier using the actual uploaded passages. All three passed citation-reference checks. An invented quotation was then rejected and its unsupported finding excluded. This checks the reference verifier, **not** the model's ability to discover disagreements or interpret them correctly. Evidence: `artifacts/synora-review/reference-check.json`.

## Next live run

The subsequent configuration and live attempt are recorded below. To rerun on the user's machine, close the existing ContextGuard server window, reopen `start.bat`, then open the saved six-source review and select **Review the evidence**. The previous server process had loaded empty key settings before configuration changed. Alternatively, from the project root run `node scripts/check-synora-review.mjs` while the restarted server is running. The script creates a separate review, uploads all six files, and writes real run/report output. Review the quotations, draft status, and coverage before accepting the findings.

## Configured-provider attempt and fixes

The user's provider configuration was found in `.env.example`. It was transferred locally into `.env`, and secret fields were cleared from `.env.example`. Key values were not printed or included in test artifacts.

The existing server was outside this session's process-control permissions. The same application was started on `127.0.0.1:8018` with the isolated test database `artifacts/synora-review/live.sqlite3`. It recognized Meta Muse Wonder, Groq, and NVIDIA. The complete browser upload and analysis action was exercised.

All three outbound HTTPS connection attempts were denied locally: the exception chain ended in `PermissionError`, errno 13 / Windows error 10013. A separate connection probe without credentials confirmed the same failure for every provider. No model response, key validity, quota, or semantic detection result can be inferred from these failures.

Two issues found during the attempt were repaired:

- The provider adapter discarded its failure details when every provider failed. It now reports safe causes such as local network permission failures, timeouts, or HTTP errors. Raw exception text, headers, response bodies, and keys are excluded. Permission failures are not retried against the same provider.
- The Synora browser runner previously exited successfully even when a configured-provider review failed. It now exits with status 1, preserves the real failure details, and checks that the failure is visible and a nonexistent report cannot be exported.

Verification after the fixes:

- All **46 backend tests passed**, including three added regression cases for safe network-denial, timeout, and all-auth-failure diagnostics. The existing nonfailing Starlette deprecation warning remains.
- The six real files uploaded through the browser with matching text and hashes, persisted after reload, and rendered in the source dialog.
- The live analysis attempt ended in a visible failure containing the network-permission cause; no invented findings were substituted. Export without a report returned HTTP 400.
- No browser page errors were recorded. The screenshot was inspected.
- The browser runner correctly exited with status 1 for this failed live review.

Latest isolated test case: `3a17de510da04422a8531532f45f2646`. Updated evidence: `artifacts/synora-review/results.json`, `case-output.json`, and `browser-output.png`.

**Live semantic output review remains pending a run from a process permitted to reach the configured providers.**

## Live Muse Wonder baseline after user restart

The user restarted the main application outside the restricted testing process. On the six uploaded files, the application successfully completed all three live stages with **Meta `muse-wonder-1.0`**. The run took approximately 65 seconds. No fallback provider was used; fallback account access remains unverified.

Baseline case: `632d885ac1964c3a8819104d65692eb4`. The real report contained three findings: a potential canvas-input conflict, missing approval evidence, and missing named owners. It rejected three records, so the expected timing and approval-policy disagreements were absent from the displayed report. All sources parsed with matching text/hashes; report rendering and Markdown export succeeded; no browser errors occurred. Baseline evidence is preserved in `artifacts/synora-review/baseline-case-output.json` and `baseline-results.json`.

Inspection identified two application problems requiring a rerun after repair:

1. Findings were rejected if any supporting citation was indexed under a different check. A date finding may legitimately cite a second check's evidence about draft/approval status. The verifier now permits such qualifying citations while still requiring valid source quotes, included checks, and at least one citation for the finding's own check. Invalid or excluded references remain rejected. Rejection details now identify the affected finding and reason.
2. Default `not_assessed` coverage fields were sent to the model before verification, resulting in a misleading limitation in an otherwise assessed report. Those fields are now withheld from model inputs; the application computes coverage after checking the evidence.

All **49 backend tests passed** after those repairs, including regression cases for qualifying citations and continued rejection of invalid references. These checks do not establish the cause of every baseline rejection because raw rejected candidates were not retained in that run.

## Final available verification

At the user's request, `start.bat` was launched by this session after the previous server was closed. The corrected app started on port 8017 and reports API version 1.0.1. The repeat six-file browser run uploaded and persisted every source, but its Meta/Groq/NVIDIA requests were blocked by local network permissions before any provider response. The runner correctly returned exit status 1. Latest failed case: `9f3d5c9bda8a44fe93417feaec23d951`, titled **Synora - fixed verifier, network-blocked rerun**.

An additional regression exercises the real six-file uploads through the actual API and SQLite with **manually annotated, controlled model outputs**. It includes all three seeded disagreements with qualifying citations from another check. All three findings survive verification; recording an answer triggers a recheck, retains the selected status/owner, preserves source hashes, exports the user statement distinctly, and undo reopens the issue. This is a functional regression, not a live detection-quality result.

- **50 backend tests passed** (`.venv/Scripts/python.exe -m pytest -q`).
- **Nine grouped browser checks passed**, with no page errors (`node scripts/browser-check.mjs`). They cover sample report, map/source preview, clarification/recheck/reload, clipboard/download, undo, own-source provider availability, real upload/failed PDF, delayed-upload navigation, and 390px mobile layout/dialog behavior.
- The browser runner now checks for each seeded topic in the actual cited text when a live report completes, and returns failure if any topic is absent. These are coarse fixture checks, not semantic accuracy measurements.
- The completed original model report is retained as **Synora - live Muse Wonder baseline**, case `632d885ac1964c3a8819104d65692eb4`, and its exported brief is `artifacts/synora-review/baseline-kickoff-brief.md`.

The final assessment is **functional regressions pass; post-fix live semantic review is not completed**. No new conflict-detection success or accuracy score is claimed for the repaired workflow. The app remains running at `http://localhost:8017`.

The user requested a completion notification to a phone number. No SMS/WhatsApp messaging tool is connected in this session, so no phone message was sent.
