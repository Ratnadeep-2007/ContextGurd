# Verification results

Latest follow-up (24 October 2026): **80 backend tests, the nine existing browser checks, and the revised clarification browser journey passed.** The form now puts the owner first, uses one context-based dropdown, and opens a textbox only for the final Other option. See [clarification verification](clarification-options.md). The three new Synora sample sources parsed successfully; generated reviews were cleared through the API for a fresh user test. The earlier project-memory browser journey passed with controlled analysis; its Mem0 REST adapter and live-service limitation are documented in [project memory](../docs/project-memory.md). The sidebar note was removed, Recent Reviews uses the available height, and provider/privacy settings are in the top-right navbar. A live six-file Synora review previously completed using Meta Muse Wonder, exposed verifier problems, and led to fixes. A fresh live inference run of those fixes is blocked by the execution environment's outbound network permissions. See [Synora test results](synora-review-results.md) for the observed findings, repairs, and limitations. The original records below describe the earlier verification stage.

Recorded: 23 October 2026. Software verification is distinct from model accuracy and user validation.

| Executed check | Result | Evidence |
|---|---|---|
| Backend regression/integration suite | 39 passed | `python -m pytest -q` |
| TypeScript and production bundle | Passed | `npm.cmd run build` in frontend |
| Clean frontend reinstall | Passed on Windows x64 with cached third-party packages | `npm.cmd ci --offline --cache .npm-cache --ignore-scripts --no-fund` |
| Sample browser → API → SQLite → report | Passed | Real installed Edge, `node scripts/browser-check.mjs` |
| Source preview and evidence map | Passed | Opens actual extracted passages and graph records |
| Clarify → recheck → reload → undo | Passed | Browser checks status, saved answer/owner, history, and reopening |
| Copy/download kickoff brief | Passed | Real clipboard write and Markdown download |
| Own-source ingestion | Passed | Browser paste/TXT upload/invalid PDF; backend tests cover PDF pages/text and DOCX tables |
| Late upload after case navigation | Passed | Controlled browser request delay cannot switch selected case |
| 390px mobile view | Passed | No horizontal overflow, navigation, native dialog Escape dismissal |
| Visual inspection | Performed | Desktop welcome/report and mobile screenshots in artifacts |
| Fixed model-evaluation bundles | 12 prepared; live evaluation NOT run | `evaluation/cases.json`, `python scripts/evaluate.py` |

The browser runner records nine grouped functional checks in `artifacts/browser-results.json`; this is not a model-accuracy score. Screenshots/downloads are ignored generated artifacts.

## Repaired code-review findings

- Empty normalized quotes could match any text; meaningful quote length is now required.
- Malformed provider envelopes bypassed fallback; malformed envelopes and schema failures now enter bounded retries/fallback.
- Distinct issues from the same page were deduplicated incorrectly; finding identity now includes exact quotes.
- Distinct conflicts inside one paragraph were rejected; two different statements may share a passage.
- Excluded checks were counted as malformed evidence; intentional exclusions no longer inflate rejection counts.
- Coverage was overstated when no evidence was extracted; insufficient-evidence status is now explicit and exported.
- Clarifications were omitted from live context; only the latest applicable case-scoped assertion now reaches roles, separately from documentary proof.
- Briefs could silently reflect an old report; pending/failed/cancelled rechecks now block export.
- A delayed child mutation could navigate back to an old case; mutation updates now check the active case.
- Rechecked forms could retain old answer/owner values; they now follow the report revision.
- Cancelled jobs could apply results later; run-ID/status guards prevent this, covered by a cancellation test.
- Small guide text and mobile off-canvas artifacts were improved after screenshot inspection.

## Not verified

No model API keys were configured: no live Meta/Groq/NVIDIA inference, provider-account access, measured detection accuracy, or real-provider failover is claimed. Adapter tests use controlled HTTP responses; the three-role integration test uses controlled outputs. The sample is fixed fictional replay through the real verifier/storage/UI.

Run `python scripts/evaluate.py --live` after configuring keys. Its coarse expected/forbidden finding-type checks do not establish semantic precision: human evidence review and baseline comparison remain necessary. User interviews and observed usability sessions are also pending.

Outbound registry HTTP was restricted. Frontend packages were installed from cached npm tarballs, without reusing existing application code. The lockfile contains public registry URLs and pinned versions; Windows x64 clean reinstall/build passed. Other operating systems and a fresh Python environment have not been tested. Exact direct Python versions are in `backend/requirements-tested.txt`.

One environment warning remains: Starlette deprecates its HTTPX TestClient compatibility. It does not fail the tests. Parser isolation has a subprocess time limit, not an OS memory quota. Scanned PDF OCR, DOCX headers/footers/tracked edits, multi-user auth, internet hosting, and forensic deletion remain outside scope.

No deployment, repository publication, submitted video, user-led final review, or final user acceptance is claimed. The running application is a local single-user build.

## Launcher follow-up

`start.bat` was executed directly from the root and from the frontend directory. A fresh start served `/`, `/api/health`, and `/openapi.json` with HTTP 200. A duplicate launch originally failed with an occupied-port error; the launcher now identifies a healthy ContextGuard instance and returns exit code 0. It also reports missing builds and unrelated port conflicts. Four focused launcher regression tests passed (`python -m pytest backend/tests/test_launcher.py -q`). The app was left running after the fresh-start check.
