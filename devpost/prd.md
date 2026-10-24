---
doc: prd
status: approved
---
# ContextGuard — Product Requirements
Authority: the user's detailed implementation brief. Learner hands-on feedback is recorded separately.

## The Core Journey
Create/sign into a local account, select project and goal, select authorized sources/dates, review parsing/routes, run analysis, inspect cited findings, assign/respond/confirm, export the Context Gap Report. Explicit fictional demo actions create labeled test sources.

## Look and Feel
Minimal native controls, readable system typography, responsive columns, solid ivory/white/forest with amber/red statuses, keyboard focus and useful guide sentences. No gradients or generic AI slogans.

## Features and Behavior
### Identity and source access
Workspace owners manage identifiable accounts; projects grant owner, decision_owner or reviewer roles. Source access is independent. Review owners manage assignment/dismissal; accountable assignees answer; only project owners/decision_owners confirm. Authorship does not imply responsibility.
### Evidence and routing
All adapters preserve workspace/source/container/item IDs, original passage, author/external identity, date, link/location, parsing state, consent and uncertainty. Routing order: explicit accessible project, approved source mapping, otherwise unknown. Model suggestions are never confirmed routes. Unknown items cannot access memory, notify assignees or produce project findings. Users may assign, keep, dismiss or create a project. Confirmed segments retain full original import and provenance; no silent full-item duplication.
### Sources
Manual upload failures retain filename/error and offer paste fallback. Explicit Vexa join/fetch controls preserve speaker/time and partial transcripts without internal STT. Slack OAuth uses minimal scopes and selected channel/thread/date pulls; revoked tokens, rate limits, edits/deletions and truncation are visible. Baileys is unofficial and stays isolated/test-only until safe live pairing is verified; manual WhatsApp import remains available. No sending or all-chat scraping.
### Goal-specific findings
Kinds: verified_fact, potential_conflict, missing_information, unsupported_assumption, possibly_outdated, unresolved_dependency, clarification_needed. Each material finding has exact source IDs/quotes, goal impact, uncertainty/alternate interpretations, a focused question and next action. Different scopes, milestones, versions or periods are not automatically contradictions. Missing-information claims describe the inspected evidence boundary.
### Assignment and resolution
One accountable assignee plus optional collaborators/watchers. Suggest only from configured responsibility or cited evidence; review owner confirms. Responses retain actor/time/explanation/evidence. Unknown answers stay open. Decision confirmation is separate, append-only and records supporting evidence/supersession; newest messages never silently replace authority. New conflicts link old decisions and reopen/create findings.
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
Generic chatbot, autonomous decisions, project-management suite, message sending, document rewriting or numerical readiness scoring.

## Open Questions
Fresh-repository model endpoints/accounts and Vexa/Slack/Baileys connections are unverified. No personal learning uncertainty or final user feedback is invented.
