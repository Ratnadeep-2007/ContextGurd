# Conversation-first reviews

This workflow is implemented with bounded processing, model consent, coverage/citation validation, project-specific reviews, successful-run unmatched-content removal, review filters and separate Word/Markdown exports. See [the current guide](conversation-workflow.md) and [verification](conversation-verification.md). Live verification of the new matching prompt remains separate from controlled tests.

## Target experience

1. Receive an authorized meeting transcript, conversation or uploaded document. Source access and external model processing require explicit consent.
2. The agent interprets the complete input against accessible project descriptions. Ordinary wording and mixed-project meetings must be supported. Long content needs coverage-aware chunks, without silently truncating and claiming full coverage.
3. Extract relevant project-specific passages. Enforce source/workspace permissions and explicit user choices before accepting any match or reading project memory. A channel mapping does not mean every sentence is relevant. Do not copy a whole mixed-project meeting into every project.
4. Ignore and remove unmatched/uncertain content from active input after successful, coverage-verified processing. It creates no review, question, assignment or project memory. A provider failure retains input for retry. Relevant exact evidence and historical decisions are preserved; no source-account deletion or secure-erasure claim is made.
5. Generate citation-verified findings per matched project, using the project goal, relevant evidence and prior confirmed decisions. This can be one or several model operations; a separate memory engine per source is unnecessary.
6. Users filter generated reviews by project, creation date, source and finding status. The separate Unknown Context tab is removed.
7. Assignees answer through contextual options or Other. Authorized decision owners confirm resolutions. Record actor, date, answer and evidence in a versioned project decision; an answer alone does not close a finding. Unknown answers stay unresolved.
8. Produce the updated Context Gap Report and, when requested, a consolidated document incorporating confirmed decisions. Cite evidence and mark unresolved issues. Export a new version rather than silently overwriting the original upload.

## Evidence and deletion

Read the complete input, then retain the relevant passages plus sufficient surrounding context, speaker/author, timestamps, segment boundaries and original source identifiers/links for each finding. Discarding unrelated content must not break citations or remove context needed to interpret an apparent conflict. Preserve common provenance across project-specific segments.

Deletion concerns ContextGuard's local content, not messages or recordings in the original source account. The source adapters remain read-only. Do not purge older reviews, imports or existing unassigned evidence as a side effect of this planning update. Cleanup must account for revisions and report dependencies and retain a discard reason without retaining the discarded content itself.

## Actual implementation

Working: automatic source registration, complete-input unit coverage and project matching, background status/retry, project-specific source grants, analysis/fallbacks, citation checks, source revisions/deletion observations, review filters, role-aware assignment/response/confirmation, versioned decisions, Markdown reports and consolidated Word/Markdown documents. Existing fictional test accounts/projects remain available.

Still required: broader live matching/accuracy evaluation, a real consented Vexa meeting/transcript/report test, a real Slack installation/selected pull and the separately scoped Baileys live runtime/pairing. Transcript fetching and Slack pulls remain explicit; no unattended meeting-completion or Slack Events worker is claimed. Limits are explicit. Historical/legacy records were not purged.

The boundary is verified with controlled model responses and fictional browser cases. This establishes workflow/permission/coverage enforcement, not infallible interpretation of arbitrary meetings. The latest fictional live attempt was denied by Windows outbound permissions before any provider response.
