# Project memory across reviews

## User flow

1. Create a review, select a project (or create one), and save the decision setup.
2. Add sources and review them. Record clarifications using a source choice or Other.
3. Create another review and select the same project. **Earlier project decisions** shows relevant recorded answers, the earlier question/review, owner, date, and original source references.
4. Analysis receives those earlier answers as historical user context. It must ask for confirmation when current documents disagree; remembered answers do not automatically resolve the new report.
5. The kickoff brief lists which earlier decisions were considered. If one of those decisions is later undone or removed, export requires a fresh recheck.

Reviews left separate have no project recall. Project assignment is explicit; a similar title does not place two reviews in the same project. Fictional sample replay does not publish decisions into project memory.

## What is saved

SQLite remains the exact record. A confirmed clarification includes its answer, optional owner, time, question, source/input fingerprint, original review, and a snapshot of supporting source passages. Only the latest applicable confirmation for an issue is available for project recall. Undo, a later unknown/dismissal/risk choice on that issue, changed inputs, a project change, or deleting its original review removes it from active recall.

The decision record and search index change in the same database transaction as the case. Source snapshots remain meaningful even if a later model run uses different finding IDs. Memory is historical context, not a replacement for source evidence or independent approval.

Local recall uses SQLite FTS5 keyword ranking, supplemented by recent decisions from the same project. It is not described as semantic search. At most eight earlier decisions are returned; AI context has a separate 12,000-character memory budget, with explicit omissions recorded in report limitations.

## Mem0 integration

The adapter uses the published **Mem0 OSS REST API**, so the ContextGuard process does not need the `mem0ai` SDK or another model SDK:

- `POST /memories`: store the exact confirmed answer with `infer: false`, project-scoped `user_id`, and decision metadata.
- `POST /search`: search using project filters.
- `DELETE /memories/{id}`: remove superseded, undone, or deleted records from the retrieval index.

Pending index operations are durable in SQLite. A single background worker processes bounded batches, with retry available at `POST /api/memory/retry` and when recall is refreshed. Index failures leave local decisions usable. Every search hit is resolved back to a current local record; remote text or filters cannot introduce another project's answer, a deleted decision, or an invented source. Revalidation also happens after an in-flight remote search.

Connect an existing Mem0 OSS server by adding these local settings to `.env`, then restart ContextGuard:

```dotenv
MEM0_BASE_URL=http://127.0.0.1:8888
MEM0_API_KEY=your-mem0-server-key
```

Use the key issued by that server (sent as `X-API-Key`). This adapter targets the OSS server contract, not Mem0 Platform's different API. Remote server URLs must use HTTPS. The Mem0 service needs its own working embedding configuration; a Muse Wonder chat key does not itself configure embeddings. Its service configuration is separate from ContextGuard's review-provider fallbacks.

The official setup and configuration are documented at:

- https://docs.mem0.ai/open-source/setup
- https://docs.mem0.ai/open-source/configuration
- https://docs.mem0.ai/open-source/features/rest-api

If connected, confirmed answer text and project/decision metadata are sent to the configured service. The UI's Providers & privacy section states this. Original source snapshots remain in the local authoritative records; recall returns those local snapshots rather than trusting a remote summary.

## Implementation paths

| Area | File |
|---|---|
| Project and decision data contracts | `backend/app/schemas.py` |
| Durable decisions, FTS5, index outbox, migration | `backend/app/store.py` |
| Mem0 REST adapter, scope checks, local fallback, background sync | `backend/app/project_memory.py` |
| Project/recall APIs and analysis context assembly | `backend/app/main.py` |
| Historical-context prompts and brief | `backend/app/workflow.py` |
| Project selector and earlier-decision panel | `frontend/src/components/ProjectMemory.tsx` |

## Verified and pending

The backend suite passed 75 tests, including project separation, local persistence, invalidation/undo/deletion, retries, an in-flight acknowledgement race, stale export blocking, and Mem0's REST request/response contract against controlled HTTP responses. Historical context reaches all three analysis stages without automatically changing a current finding's status.

The dedicated browser journey passed in an isolated database with explicitly scripted analysis. It used the six real synthetic Synora files for an earlier answer, displayed that answer in a new same-project review, preserved source references and reload behavior, checked a different project receives no answer, and verified project creation and mobile layout. Evidence is in `artifacts/project-memory/`.

**A real Mem0 service has not been started or connected in this environment.** Installing the SDK was unavailable from this session, and the Docker daemon was not running. Semantic retrieval quality and real Mem0 embeddings are not verified. The cross-review feature runs using local recall until a service is configured. Browser fixture analysis and controlled HTTP tests are not live model/Mem0 accuracy results.
