# ContextGuard architecture

This describes the fresh implementation. The [conversation-first workflow](conversation-workflow.md) is implemented: adapters feed private intake jobs, code validates unit coverage/project boundaries, project reviews read only their own decisions, and successful processing clears unmatched input. Source adapters share project memory. The diagram below describes compatible legacy manual APIs; the old registration/inbox UI is removed.

```mermaid
flowchart TD
    UI[Local browser: project + review goal] --> Auth[Session + workspace/project/source authorization]
    Auth --> Manual[Manual text / TXT / MD / PDF / DOCX]
    Auth --> Vexa[Vexa join/fetch controls: external transcript]
    Auth --> Slack[Slack OAuth + selected bounded pulls]
    Auth --> WA[WhatsApp manual / experimental read-only Baileys worker]
    Manual --> Evidence[Shared Passage + Delivery contract]
    Vexa --> Evidence
    Slack --> Evidence
    WA --> Evidence
    Evidence --> Raw[Preserve original selected import + source revisions]
    Raw --> Route[Explicit project, else approved mapping]
    Route -->|unconfirmed| Unknown[Leave unassigned: no project analysis or memory]
    Unknown -.->|only if a user explicitly routes it later| Route
    Route -->|confirmed + authorized| DB[SQLite project evidence + versioned decisions]
    DB --> Review[Goal/date/source snapshot]
    Review -->|explicit transfer consent| LLM[Muse Wonder → Groq → NVIDIA]
    LLM --> Verify[Schema + exact quote + scope boundary checks]
    Verify --> Report[Context Gap Report + visible status rules]
    Report --> Assign[Review owner confirms accountable assignee]
    Assign --> Response[Assignee response: still open]
    Response --> Confirm[Authorized decision owner confirms]
    Confirm --> Decision[Append decision with actor/date/evidence/supersession]
    Decision --> DB
    Report --> Export[Stored Markdown export]
```

## Actual code boundaries

- `app/contracts.py`: common source and model schemas. Strict booleans prevent the string `"false"` from acting as consent or a known answer.
- `app/storage.py`: one local SQLite records table, JSON entity values, a process lock and transaction per command. This is a fresh schema, not Synora's schema.
- `app/service.py`: accounts, source grants, project roles, deduplication/revisions, explicit/mapped/unknown routing and confirmed original-source segments.
- `app/adapters.py`: independent manual/Vexa/Slack/WhatsApp event readers. No message-send or transcription implementation.
- `app/providers.py`: bounded external calls and shared output validation. Primary endpoint/model are configured rather than guessed.
- `app/review.py`: authorized snapshot, prior-decision recall, citation checks, comparison-boundary checks, assignments, responses, confirmation and export.
- `app/api.py`: local-origin authentication, explicit operations, document snapshot reconciliation, OAuth state and protected token handling.
- `web/app.js`: source selection, inbox, team controls, exact passages and context-based answers. All source text is escaped; external links accept only HTTP(S).

## Boundaries that must stay visible

Unknown context cannot read or write project decisions. A model suggestion never changes a route. A source grant never grants access to an unrelated project's routed evidence. A response never implicitly resolves a finding. A source revision, absent document passage or deleted original invalidates dependent snapshots/segments. Earlier confirmed decisions remain inspectable even when their supporting source is no longer current.

Slack pulls are bounded and never claim full workspace coverage. A missing item from a complete selected pull becomes unavailable/uncertain, not a proven deletion; channel history does not invalidate thread-only replies. Actual deletion events create tombstone revisions. Vexa partial text remains partial, and empty speakers remain unattributed.

Baileys experimental pairing now uses an admin-only private stdio Node worker, AES-GCM session encryption with a DPAPI-protected key, explicit chat selection and no history sync. Package installation/DPAPI were denied in this session; real pairing is unverified. See whatsapp-live.md. Vexa/Slack REST/OAuth contracts are implemented and tested with controlled responses; real services and accounts remain unverified. Windows DPAPI token protection was denied in this execution environment, and OAuth correctly refused plaintext persistence.

## Current conversation intake

`app/intake_api.py` creates sources internally for uploads/notes, Vexa links and selected Slack captures. `app/intake.py` stages input, validates every unit exactly once in ordered bounded batches, enforces explicit scopes/source mappings and creates exact project evidence. Only then does analysis read memory. Network calls hold no database transaction. Polling exposes progress, not raw input. Success clears unmatched input; failure retains it for explicit retry. Source/project access is rechecked after model calls; changed profiles/maps fail instead of silently rerouting.

`web/workspace.js` renders Sources connections and Project Reviews capture/library. `web/app.js` polls jobs and applies review filters. `app/exports.py` generates Word/Markdown from confirmed decisions, open issues and original relevant evidence without another model call or overwriting an upload.

## Legacy unclear project content

Legacy ingestion/routing endpoints remain compatible with existing unassigned records, which were not purged. New intake removes unmatched units only after successful analysis, without a classification question or memory lookup. The requested diagram omits the missing/partial-content panel; actual connection/parsing failures remain visible and never become fabricated successful reviews.
