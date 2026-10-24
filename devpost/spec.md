---
doc: spec
status: approved
---
# ContextGuard — Technical Spec

## How This Works, In Plain Language
The browser sends sources to a local Python server. The server preserves source text, runs a bounded review, checks references, and saves the case in SQLite. Sample mode replays a fixed fictional case and uses the same verifier/resolution logic. Live mode calls the selected providers; it never silently switches to sample results.
## The Core Journey Through the System
PRD ref: prd.md > The Core Journey. Create case → parse sources → start analysis job → poll actual stage → render report/evidence → save resolution → recheck → persist revision → export brief.
## Stack
React/TypeScript/Vite, ordinary CSS, Lucide icons. FastAPI/Pydantic/httpx, pypdf/python-docx, sqlite3. This carries forward the approved plan; direct httpx adapters avoid a provider gateway. Tests: pytest, controlled HTTP transports, browser checks with Playwright against installed Edge.
## Where It Runs and How Someone Tries It
Local single-user only. Python 3.11+, Node 22.12+ (Node 24 recommended). `start.bat` creates the virtual environment, installs dependencies and builds the frontend when needed. A broken existing environment is preserved with repair guidance. `.venv/Scripts/python.exe scripts/dev.py` starts API and Vite on loopback; open http://localhost:5173. `.venv/Scripts/python.exe scripts/serve.py` serves a complete built frontend and API at http://localhost:8017. Configure keys in root .env for live analysis. No keys are needed for the labeled sample. Public source is at https://github.com/Ratnadeep-2007/ContextGurd; a public app deployment is not required for this local POC.
## Look and Feel
Canvas #f6f5f0; surfaces #fff; primary #234c3d; charcoal #252b28; muted #69716b; rules #e3e6df. Serif display accents and system sans body, no remote font requirement. All controls have labels and nearby guidance; keyboard focus, responsive stacking, reduced-motion support, no gradients.
## Components
Frontend: case navigation, setup/source panel, project picker/earlier-decision panel, criteria editor, analysis progress, findings list, evidence detail, owner-first clarification dropdown with conditional Other textbox, history, brief dialog, navbar settings. Backend: models, parser, SQLite store, project-memory/Mem0 adapter, provider adapter, verification/workflow, fixture data, API.
## Data Model
SQLite stores versioned JSON case snapshots plus projects, confirmed project decisions, a decision_search FTS5 index, and durable memory_index_jobs. Case snapshots contain stable document/passage IDs, checks, evidence, findings, resolution events and runs. A resolution preserves its choice ID/action/answer, owner, input fingerprint and original source snapshot. Each mutation validates version; background jobs work on snapshots and reject stale/cancelled revisions. Original passages remain unchanged; changed inputs invalidate old report/application of answers. No API keys are stored in case JSON.

Only current applicable user confirmations enter project recall. Retrieval is project-scoped, excludes the current review, returns at most eight decisions and supplies at most 12,000 serialized characters to the model, with explicit omissions. Historical context remains separate from current documentary evidence. Mem0 search IDs are checked against current local decisions after the remote call, preventing stale or cross-project results. Index operations are asynchronous and durable; local recall works without the remote service.
## File Structure
`backend/app/`: schemas.py, ingestion.py, ingestion_worker.py, store.py, project_memory.py, providers.py, workflow.py, sample.py, main.py.
`backend/tests/`: API, parsing, verification, persistence, provider, and fixed-case evaluations.
`frontend/src/`: App.tsx, components, api.ts, types.ts, styles.css.
`scripts/`: dev.py, serve.py, browser-check.mjs, browser-clarification-check.mjs, browser-project-memory-check.mjs, verify-release.mjs, audit-repository.py. `evaluation/`: fixed cases/results. `devpost/`: planning, build/submission records and offline app-map.html. `samples/synora-three-docs/`: three synthetic user-upload examples.
## External Services and Dependencies
POST chat/completions with system/user messages and JSON schema to Meta https://api.meta.ai/v1 (`MODEL_API_KEY`, muse-wonder-1.0), Groq https://api.groq.com/openai/v1 (`GROQ_API_KEY`, openai/gpt-oss-120b), optional NVIDIA https://integrate.api.nvidia.com/v1 (`NVIDIA_API_KEY`, nvidia/nemotron-3.5-super-vl-120b-a12b). Provider docs and research links are in the validated idea document. Strict schema where supported; Pydantic always validates. Bound call sizes, deadlines, retries, and costs. No free-tier guarantees.

Optional Mem0 OSS REST service: `MEM0_BASE_URL`, `MEM0_API_KEY`; POST /memories with infer=false, POST /search with project filters, DELETE /memories/{id}. The service needs its own working embedding configuration. No mem0ai SDK, model weights, or service runtime is bundled in ContextGuard. See docs/project-memory.md.
## Important Failure Modes
No keys → explicit disabled live path. Parser failure → retained visible failed source. Invalid citations → reject finding and record the reason; qualifying valid evidence can come from another included check. Provider failures → bounded enabled fallback then safe diagnostics distinguishing network permission, timeout, HTTP and schema failures. Restart during run → interrupted job status, user can retry. Mem0 failure → durable retry and local recall. Stale earlier project context → brief export blocked until recheck. Incomplete frontend build → API remains usable independently; the production launcher reports the missing build. A broken virtual environment is preserved rather than deleted automatically.
## What Was Simplified and Why
Local single-user case snapshots avoid auth and cloud storage. Fixed sample is labeled fixture replay rather than fake AI. A compact data-driven graph avoids a graph database. Full rerun after clarification is safer than speculative incremental dependencies.
## Decisions and Open Issues
Primary model/fallback choices and UI revisions were user-selected/accepted. Colors/layout are implementation choices within those constraints. Initial real Muse Wonder inference completed; current live verification was attempted again with three synthetic sources, but all providers were blocked by local Windows network permissions. Current functional tests, controlled HTTP contracts, browser flows and a clean cached frontend install pass. Fresh online Python installation, current live model quality, live fallback access and live Mem0 semantic retrieval remain unverified. Accounts/role assignment are deferred proposals. Exact evidence is in evaluation/release-readiness.md and docs/build-history.md.

