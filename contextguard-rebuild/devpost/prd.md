---
doc: prd
status: approved
---
# ContextGuard — Product Requirements
Authority: the user's detailed implementation brief. Learner hands-on feedback is recorded separately.

## The Core Journey
Implemented journey: create/describe projects → capture authorized content → interpret all input units → validate project-specific matches → generate cited reviews → filter by project/source/creation date/status → assign/respond/confirm → retain versioned decisions → export a report or consolidated Word/Markdown document. The source is registered internally. See [conversation workflow](../docs/conversation-workflow.md). Automatic matching uses model interpretation and remains fallible; controlled/browser verification is distinct from live model/source verification.

## Look and Feel
Minimal native controls, native Segoe UI typography, responsive columns, the selected Claude Amber palette: warm white surfaces, dark text, terracotta actions and amber/red statuses, visible keyboard focus and brief guide sentences. Square corners throughout; no gradients, decorative shadows or generic AI slogans.

Current user-requested redesign supersedes the earlier ivory/sage/serif presentation: warm white navigation and white work surfaces, warm neutral borders, terracotta actions, square components and consistent Segoe UI headings. Reviews use divided rows rather than rounded cards; the project picker and review library have explicit section rules. Source quotations remain visually separate from controls. The report uses a selectable findings index beside one detail with All/Needs attention/Recorded filters; mobile stacks those surfaces and exposes workspace navigation through a keyboard-operable drawer. Independent presentation code preserves the rebuild's team/source/confirmation behavior. Optional collaborators/watchers are collapsed to keep the primary clarification task clear.

Current project and project creation sit above the cards in Project Reviews, with one project filter shared by the library. The sidebar contains navigation and recent reviews. Visible copy is restricted to titles, factual state and brief guidance; duplicated slogans and instructions are removed.

## Features and Behavior
### Processing visibility
Project Reviews shows upload and processing status above Add context immediately on submission. It uses real server stages and counters, separate matching/analysis progress, an elapsed clock, reload restoration and explicit completion/failure actions. Duplicate submissions for an active project job are prevented. Full passage matching does not mean review completion. Earlier jobs remain in a collapsed history. Each retry starts a fresh persisted attempt clock and increments the attempt number while preserving the original upload date. Legacy jobs without an attempt start show Since original upload. Local network-denial errors explain normal-user startup and retain input; a failed job offers retry without presenting an intermediate review as completed. See [processing behavior](../docs/processing-ui.md) and [Windows recovery](../docs/windows-network-recovery.md).

### Identity and source access
Workspace owners manage identifiable accounts; projects grant owner, decision_owner or reviewer roles. Source access is independent. Review owners manage assignment/dismissal; accountable assignees answer; only project owners/decision_owners confirm. Authorship does not imply responsibility.
### Evidence and routing
All adapters preserve workspace/source/container/item IDs, retained exact passages, author/external identity, date, link/location, parsing state, consent and uncertainty. Explicit project scope is authoritative; otherwise approved source mappings constrain eligible routes. The model reads every unit in ordered bounded batches with neighboring context, proposes project matches, and must return each unit exactly once. Code rejects missing/duplicate IDs, inaccessible projects and mapping violations before any memory lookup. Relevant units become project-scoped sources; no full mixed transcript is duplicated across projects. After every project analysis succeeds, unmatched/uncertain units and the pending raw input are removed from active intake records. A failed run retains input for explicit retry. Older evidence/decisions are preserved. There is no Unknown Context tab or compulsory project-classification question. Legacy routing endpoints remain for compatibility with existing records.
### Sources
Sources contains connection status/check controls, Slack OAuth, experimental WhatsApp QR pairing, setup status and selected-chat controls, and Vexa meeting-link/passcode Join/Stop/Fetch controls. Uploads/pasted notes and selected Slack pulls live in Project Reviews. Manual parsing errors offer readable-text fallback. Vexa consumes external transcripts without duplicate STT and never joins silently. Channel/thread/date selection and minimum read scopes constrain Slack. Partial Slack pulls are rejected instead of treated as complete. Observed edits/deletions preserve revisions and invalidate affected reports. Baileys is isolated behind a private read-only Node worker with explicit chat selection and protected session storage; real dependency/phone verification remains pending and manual export ingestion works. No sending or all-chat scraping.
### Goal-specific findings
Kinds: verified_fact, potential_conflict, missing_information, unsupported_assumption, possibly_outdated, unresolved_dependency, clarification_needed. Each material finding has exact source IDs/quotes, goal impact, uncertainty/alternate interpretations, a focused question and next action. Different scopes, milestones, versions or periods are not automatically contradictions. Missing-information claims describe the inspected evidence boundary.
### Assignment and resolution
One accountable assignee plus optional collaborators/watchers. Suggest only from configured responsibility or cited evidence; review owner confirms. Responses retain actor/time/explanation/evidence. Unknown answers stay open. Decision confirmation is separate, append-only and records supporting evidence/supersession; newest messages never silently replace authority. New conflicts link old decisions and reopen/create findings.
### Consolidated findings and repeat processing
Findings about the same decision should appear as one ticket with combined exact citations and related questions. Stable issue keys and conservative normalized matching consolidate within compatible comparison boundaries; facts and different versions remain separate. An unchanged successful review is reused; a failed intake retry reuses its project review record and cannot overwrite human responses. Semantic grouping remains fallible. Citation rejection marks processing failed. See [duplicate handling](../docs/conflict-deduplication.md).

### Context Gap Report
Goal, dates, analyzed sources, connection/parsing failures, prioritized findings with passages/links, impact/questions/actions, owners/responses, decisions/changes and limitations. Ready requires a successful analysis, usable complete evidence and no open findings; Ready with actions allows only low/medium open findings; Needs clarification covers high open findings, incomplete evidence or failed/unverified analysis. No numerical score. Fixture reports always say test mode.

## States and Boundaries
Empty/failed input offers paste fallback. Unknown routing blocks project memory. Provider failure produces no fabricated substitute. Edits/deletions preserve history and invalidate affected report snapshots. Authentication, workspace, project and source grants precede every read/mutation/export. Explicit source operations/live analysis disclose external transfer.

## Product Decisions
Current user brief is authoritative. Local FastAPI/SQLite/native browser UI is an engineering choice to minimize Windows setup, not an invented learner preference.

## What We're Building
Core goal-review/resolution loop, team authorization and routing contracts, manual ingestion and isolated adapter clients with truthful test modes. Real-account/live-model verification is distinct acceptance work.

## Deferred From the POC
Enterprise identity, unattended capture and production Baileys operation pending actual service verification.

## Non-Goals
Generic chatbot, autonomous decisions, project-management suite, message sending, silently overwriting original documents or numerical readiness scoring. Consolidated documents are separate exports combining confirmed decisions, unresolved questions and the retained source evidence; no missing facts are invented.

## Current Verification Boundary

As of October 26, 2026, the six-document Synora intake has not completed successfully: the latest attempt failed at 0/82 passages because all providers were blocked by local Windows/network permissions. An earlier attempt reached analysis but failed citation validation. Historical provider-only successes below do not certify this current workflow. Recovery requires a normal-user launch and explicit retry, followed by inspection of citations and outputs.

## Open Questions
Model endpoints/accounts are live-verified with fictional documents for Muse Wonder and Groq, and for the controlled-failure fallback via NVIDIA (NVIDIA-as-primary is latency-bound; see docs/live-testing.md). Vexa/Slack/Baileys live connections remain unverified and blocked on authorized account configuration. No personal learning uncertainty or final user feedback is invented.

## Single-project demo refinement

The requested local demo retains Synora only, with one clearly fictional six-finding review and four named mock members. Ratnadeep alone is admin/project owner. Team shows members, roles and responsibilities without account/configuration forms. Current project scopes both browsing and manual document/text ingestion; All projects is browsing-only. Sample opening is idempotent. Source controls preserve the meeting link, clear passcodes and report verified connection outcomes. The latest recorded gateway probe was unreachable; a self-hosted Vexa configuration was subsequently recorded, but a real authorized meeting-to-report test remains pending. Slack account verification is also pending; configuration alone is not live success.


## Current WhatsApp direction

Experimental live Baileys pairing is implemented as a separate private Node worker with QR authorization, explicitly selected chats, text-only bounded ingestion and manual-export fallback. Sources manages pairing/selection; Project Reviews processes selected live text against Current project. No full-history sync or send/reply capability is exposed. Local session credentials require AES-GCM encryption and a Windows DPAPI-protected vault key; protection failure blocks pairing. Pending duplicate/edit/delete events are handled; already captured reviews remain evidence snapshots and are not automatically updated by later WhatsApp edits/deletes. Runtime installation, an actual phone scan, reconnect and native dependency behavior remain live-verification requirements. Current session npm/DPAPI access was denied. See docs/whatsapp-live.md and docs/baileys-research.md; earlier disabled-runtime statements are superseded by this section, not evidence of a verified connection.
