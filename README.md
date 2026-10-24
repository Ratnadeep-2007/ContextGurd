# ContextGuard

A local project-kickoff review workspace. Supply a decision and sources, inspect evidence-linked gaps, record clarifications, and prepare a kickoff brief.

Built from a new implementation in this workspace. No Synora application code was used. The UI uses solid ivory/forest/charcoal colors, locally bundled fonts, responsive layouts, and guidance alongside actions.

## Run it

Requires Python 3.11+ and Node.js 22.12+ (Node 24 recommended).

**Easiest (Windows): double-click `start.bat`** (or run it from a terminal). On the first run it sets everything up for you: it creates `.venv`, installs the pinned Python packages, and builds the web UI. Later runs skip setup and start immediately. Your browser opens at **http://localhost:8017** once the app is ready; keep the launcher window open while you use the app and press Ctrl+C there to stop it. If anything is missing (Python, Node.js, or a free port 8017), the window stays open and tells you exactly what to fix. Set `CONTEXTGUARD_NO_BROWSER=1` to skip auto-opening the browser.

Manual setup, if you prefer it or are not on Windows:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements-tested.txt
cd frontend
npm.cmd ci
npm.cmd run build
cd ..
.venv\Scripts\python.exe scripts/serve.py
```

The frontend build is served by FastAPI on the same origin; there is no second production server. Keep it on localhost: this is a single-user application without authentication.

`start.bat` works from any working directory and always uses the project's own `.venv`, never a random `python` on PATH. A second launch recognizes a healthy ContextGuard instance, opens the browser, and exits successfully instead of failing on an occupied port. If another service owns port 8017, the launcher reports the conflict without stopping that service.

If Python in an existing `.venv` cannot run, the launcher preserves it and asks you to rename it to a backup before retrying. It does not automatically delete the environment. An incomplete frontend build also produces an explicit repair message.

Development: `python scripts/dev.py` starts the API on 8017 and Vite on http://localhost:5173. Ctrl+C stops both. If using the virtual environment, invoke `.venv\Scripts\python.exe scripts/dev.py` instead. These commands work from the repository root; PowerShell does not need script-execution policy changes when using `npm.cmd`.

## Try the complete sample

Choose **Try a sample review**. The fictional Fieldwork case opens a source-linked report with a release-date disagreement, missing approval evidence, an unresolved payment dependency, and an unsupported SMS estimate assumption.

Open the release-date finding, inspect the quotes, enter a clarification, and choose **Save & recheck**. The answer persists after reload. **History** lets you undo it. **Prepare brief** copies or downloads a Markdown brief, including source locations and uncertainties. Review checks can be excluded with a reason. The Map view traces selected findings to their sources.

**The sample is fixed fixture replay, not live AI and not a detection benchmark.** It uses the actual citation verifier, storage, resolution, report, graph, and export paths. Its goal and source files are fixed to keep the replay honest. Start a new review for your own inputs.

## Clarification choices and saved decisions

The clarification form starts with **Who can clarify this?**, followed by one **Choose an answer** dropdown. Source answers and contextual decisions appear in the same dropdown; **Other** is last and opens a custom-answer field. Contextual decisions can keep missing information or dependent work open, dismiss a finding, or record accepted risk. These are user choices, not invented document facts. New live reports request concise competing values or statements; generated source options are kept only if their text is present in every cited evidence quote. Older conflict reports can offer exact verified source statements.

Saving a choice records its text, original passage locations, owner, timestamp, and input fingerprint in the review's local decision history, then starts a recheck. A custom answer is saved as a user statement. History supports undo. Memory is scoped to that review and the same inputs; changing sources or the goal requires a fresh review and does not automatically reuse old answers.

**Project memory across reviews:** select or create a project in review setup and save it. Later reviews assigned to that same project can recall earlier confirmed clarifications with their owners, dates, and source quotes. The AI receives them as historical user context and asks for reconfirmation when new documents differ. Separate projects and fictional sample replay do not share answers. Undo, changed inputs, and deletion remove a decision from active recall. See [project-memory setup and verification](docs/project-memory.md).

Local project recall works immediately through SQLite keyword/recent retrieval. The Mem0 OSS REST adapter adds a semantic index when a Mem0 server is configured with `MEM0_BASE_URL` and `MEM0_API_KEY`. No Mem0 service is running in the recorded environment; its HTTP contract was tested with controlled responses, not live embeddings. Index outages retain local recall and durable retry jobs.

After a successful recheck, **Prepare brief** groups recorded clarifications separately from unanswered decisions and accepted risks. It includes status counts, answers, owners, selected source statements and locations, original evidence, check coverage, and limitations. Copy it or download Markdown. Original source documents are preserved.

Source choice, Other, reload, history/undo, and an all-clarified export were verified in the browser with fictional sample replay. See [clarification verification](evaluation/clarification-options.md). Live generation of the new concise choices has not been verified against a real provider in this restricted session.

For a fresh own-source test, upload the three files in [the Synora sample folder](samples/synora-three-docs). The [sample guide](samples/synora-three-docs-guide.md) includes the suggested goal/scope and intended cases: conflicting dates, missing approval, an unsupported budget assumption, a pending dependency, an outdated task reference, and ambiguous acceptance wording.

## Enable live AI

Copy `.env.example` to `.env`. Enter keys locally; never paste them into chat or commit them. Restart the server after changing configuration.

```dotenv
MODEL_API_KEY=your-meta-key
META_MODEL=muse-wonder-1.0
GROQ_API_KEY=your-optional-groq-key
GROQ_MODEL=openai/gpt-oss-120b
NVIDIA_API_KEY=your-optional-nvidia-key
NVIDIA_MODEL=nvidia/nemotron-3.5-super-vl-120b-a12b
LLM_FALLBACK_ORDER=groq,nvidia
```

Meta is preferred. If permitted in review setup, configured Groq and NVIDIA fallbacks are attempted after bounded retries. If Meta is absent, an enabled configured fallback can run the review. Disabling fallbacks requires Meta. Provider settings show configured keys by presence only, never their values; key presence does not establish access or quota.

Live review sends the goal and source excerpts through three typed stages: Planner, Evidence, and Challenge. Deterministic checks validate quote existence, IDs, conflict reference counts, deduplication, report structure, and resolution scope. JSON validity and exact quotations cannot establish semantic correctness. Models may still miss issues, misunderstand scope, or flag false positives.

Meta/Groq use JSON Schema output; NVIDIA uses JSON object output plus independent validation. Token parameters and errors remain provider-specific. No silent fixture fallback occurs. A six-source Synora test completed all three live stages using Meta Muse Wonder. Its initial report omitted seeded issues and exposed verifier problems that were repaired; the corrected verifier has passed controlled regression checks, while a fresh live run of the repairs remains blocked by this session's outbound network permissions. See [the detailed Synora test results](evaluation/synora-review-results.md). NVIDIA's selected model is early access; confirm current access and evaluate it before relying on it. See the validated technical-plan document for linked provider research.

## Own sources and boundaries

- PDF, DOCX, UTF-8 TXT/Markdown, or pasted notes.
- Eight sources per review; 8 MB per file, 30 pages per PDF, 60,000 characters per source, 90,000 per review. Live requests have a further serialized context cap and fail explicitly if exceeded.
- PDF references are physical pages/passages. DOCX references are paragraphs/table rows, not invented page numbers.
- DOCX body paragraphs and tables are included. Headers, footers, comments, and tracked edits are not assessed.
- Scanned pages need OCR, which is not included. Empty/failed pages are visible; partial documents remain qualified.
- Upload parsing runs in a subprocess with a 25-second limit. This is a time limit, not a hardened memory sandbox; use trusted, non-sensitive demo documents.
- Goal/source/check changes invalidate reports. Historical answers are bound to the exact input fingerprint and are not automatically applied to changed inputs. Excluding a check needs a reason.
- A confirmation is a user assertion; a dismissal is a recorded relevance choice; risk acceptance does not close the underlying gap. Only the selected issue's status is updated. Full rechecks can change related questions using user assertions.
- A previous report remains visible if a recheck fails, but export is blocked until a successful current run. The app never certifies readiness or automatically approves/sends anything.

## Storage and privacy

`data/contextguard.sqlite3` stores extracted text, sources, reports, resolution history, and run metadata. Uploaded original bytes are not retained on disk. API keys are read server-side from the environment. No analytics or external font/CDN calls are required. Live excerpts leave the device for enabled providers. Deleting a case removes it from the logical database but does not promise forensic removal from SQLite free pages, disk backups, or provider logs.

SQLite stores optimistic case revisions to reject stale writes. Runs interrupted by server restart become retriable failed runs. At most two jobs run simultaneously. The app rejects non-local Host headers and cross-origin writes. This is not a multi-tenant or internet-ready security boundary; add authentication, tenant isolation, rate limiting, and a hardened parser environment before public hosting.

## Test and evaluate

```powershell
.venv/Scripts/python.exe -m pytest -q
cd frontend
npm.cmd run build
cd ..
.venv/Scripts/python.exe scripts/serve.py
# In another terminal, while the server is running:
node scripts/browser-check.mjs
```

Browser verification uses Playwright and installed Microsoft Edge (`msedge`). If Edge is unavailable, install it or adapt the script to an installed Playwright browser. Screenshots and downloaded briefs go to ignored `artifacts/`. Browser checks create local sample and upload-test cases; these can be deleted from the UI.

`python scripts/evaluate.py` checks that 12 fixed bundles are ready without sending data. `python scripts/evaluate.py --live` sends fictional bundles to configured providers and incurs API usage. Its coarse expected/forbidden finding-type checks do not measure semantic evidence precision; human evidence review remains required. Results are written to `artifacts/live-evaluation.json` only when executed.

Recorded checks and known limitations: [evaluation/results.md](evaluation/results.md). Local sample/API/browser verification is distinct from live model evaluation, user demand research, and clean-machine installation verification.

Latest release audit: [evaluation/release-readiness.md](evaluation/release-readiness.md). Tests use a separate bootstrap database and API-only test applications, so running them does not interrupt a user's normal review or depend on a concurrent frontend rebuild. On macOS/Linux, use `.venv/bin/python` instead of the Windows executable above.

## Where to change things

| Area | Code |
|---|---|
| Workspace and navigation | `frontend/src/App.tsx` |
| Inputs, preview, criteria | `frontend/src/components/Setup.tsx` |
| Findings, map, answers, history, brief | `frontend/src/components/Report.tsx` |
| Visual theme and responsive layout | `frontend/src/styles.css` |
| API and job boundaries | `backend/app/main.py` |
| Evidence verification, orchestration, brief | `backend/app/workflow.py` |
| Providers, schema compatibility, retries | `backend/app/providers.py` |
| Source parsing and isolated worker | `backend/app/ingestion.py`, `ingestion_worker.py` |
| SQLite snapshots and revisions | `backend/app/store.py` |
| Fictional replay | `backend/app/sample.py` |

The offline [app map](devpost/app-map.html) follows the actual clarification action through UI, API, and verification.

## Hackathon work

The official Devpost Learn Skill Pack was cloned under ignored `tools/learn-ai-basics` and read directly in the coding agent. Its guidance was partially applied to the existing approved idea and implementation; a complete original 1-start through 6-ship sequence is not claimed. `devpost/scope.md`, `prd.md`, `spec.md`, and `checklist.md` record the plan, accepted changes and remaining learner checkpoints. Public source is at https://github.com/Ratnadeep-2007/ContextGurd with consolidated initial commit `2b6df12`; subsequent local audit updates require their own publication checkpoint. User screenshots and requested revisions are recorded as feedback, not a formal user study or final ready-to-ship sign-off. See [build history](docs/build-history.md) and the current checklist.

Before submission, complete the final hands-on review, validate the current live flow from a process with provider access, record the functioning demo, publish prepared repository updates, and write your own submission/exit-survey answers. No completed Devpost submission or public demo-video URL is recorded. Public app deployment is optional for this local proof of concept.

## License

New ContextGuard application code is MIT licensed. See `LICENSE` and `THIRD_PARTY_NOTICES.md`. Dependency code, fonts, APIs, and model weights retain their respective licenses and terms.
