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
Local single-user only. Python 3.11+, Node 22+. `python scripts/dev.py` starts API and Vite on loopback; open http://localhost:5173. `python scripts/serve.py` serves the built frontend and API at http://localhost:8017. Configure keys in root .env for live analysis. No keys needed for the labeled sample. No deployment or publishing is authorized here.
## Look and Feel
Canvas #f6f5f0; surfaces #fff; primary #234c3d; charcoal #252b28; muted #69716b; rules #e3e6df. Serif display accents and system sans body, no remote font requirement. All controls have labels and nearby guidance; keyboard focus, responsive stacking, reduced-motion support, no gradients.
## Components
Frontend: case navigation, setup/source panel, criteria editor, analysis progress, findings list, evidence detail, resolution form, history, brief dialog, settings dialog. Backend: models, parser, SQLite store, provider adapter, verification/workflow, fixture data, API.
## Data Model
One SQLite case snapshot table with versioned JSON; stable document/passage IDs, checks, evidence, findings, resolution events, analysis runs. Each mutation validates version; background jobs work on snapshots and reject stale revisions. Original passages remain unchanged; deleting/replacing content invalidates the report and answers. No secrets stored in case JSON.
## File Structure
`backend/app/`: schemas.py, ingestion.py, store.py, providers.py, workflow.py, sample.py, main.py.
`backend/tests/`: API, parsing, verification, persistence, provider, and fixed-case evaluations.
`frontend/src/`: App.tsx, components, api.ts, types.ts, styles.css.
`scripts/`: dev.py, serve.py, browser-check.mjs. `evaluation/`: fixed cases/results. `devpost/`: artifacts and app-map.html.
## External Services and Dependencies
POST chat/completions with system/user messages and JSON schema to Meta https://api.meta.ai/v1 (`MODEL_API_KEY`, muse-wonder-1.0), Groq https://api.groq.com/openai/v1 (`GROQ_API_KEY`, openai/gpt-oss-120b), optional NVIDIA https://integrate.api.nvidia.com/v1 (`NVIDIA_API_KEY`, nvidia/nemotron-3.5-super-vl-120b-a12b). Provider docs and research links are in the validated idea document. Strict schema where supported; Pydantic always validates. Bound call sizes, deadlines, retries, and costs. No free-tier guarantees.
## Important Failure Modes
No keys → explicit disabled live path. Parser failure → retained visible failed source. Invalid citations → reject finding and record limitation. Provider failures → bounded enabled fallback then clear error. Restart during run → interrupted job status, user can retry.
## What Was Simplified and Why
Local single-user case snapshots avoid auth and cloud storage. Fixed sample is labeled fixture replay rather than fake AI. A compact data-driven graph avoids a graph database. Full rerun after clarification is safer than speculative incremental dependencies.
## Decisions and Open Issues
Primary model and fallback choices are user-selected/accepted. Colors and component layout are reversible implementation choices within user constraints. Genuine unknown: real provider behavior and semantic quality without keys. Test adapters with controlled responses now; record live checks as pending.

