# Conversation-first reviews

The user's latest clarification updates the earlier leave-unassigned design. This is the target workflow; automatic processing, routing, deletion and consolidated-document generation are not yet implemented.

## Target experience

1. Receive an authorized meeting transcript, conversation or uploaded document. Source access and external model processing require explicit consent.
2. The agent interprets the complete input against accessible project descriptions. Ordinary wording and mixed-project meetings must be supported. Long content needs coverage-aware chunks, without silently truncating and claiming full coverage.
3. Extract relevant project-specific passages. Enforce source/workspace permissions and explicit user choices before accepting any match or reading project memory. A channel mapping does not mean every sentence is relevant. Do not copy a whole mixed-project meeting into every project.
4. Ignore and delete confidently unrelated content from ContextGuard after successful processing. It creates no review, question, assignment or project memory. A provider failure or extraction error does not mean the content is unrelated. Uncertain matches create no project finding or memory write; the safe disposal policy for uncertain matches needs implementation rather than a guessed project.
5. Generate citation-verified findings per matched project, using the project goal, relevant evidence and prior confirmed decisions. This can be one or several model operations; a separate memory engine per source is unnecessary.
6. Let users filter generated reviews by project, date, source and finding status. No separate Unknown Context tab is planned.
7. Assignees answer through contextual options or Other. Authorized decision owners confirm resolutions. Record actor, date, answer and evidence in a versioned project decision; an answer alone does not close a finding. Unknown answers stay unresolved.
8. Produce the updated Context Gap Report and, when requested, a consolidated document incorporating confirmed decisions. Cite evidence and mark unresolved issues. Export a new version rather than silently overwriting the original upload.

## Evidence and deletion

Read the complete input, then retain the relevant passages plus sufficient surrounding context, speaker/author, timestamps, segment boundaries and original source identifiers/links for each finding. Discarding unrelated content must not break citations or remove context needed to interpret an apparent conflict. Preserve common provenance across project-specific segments.

Deletion concerns ContextGuard's local content, not messages or recordings in the original source account. The source adapters remain read-only. Do not purge older reviews, imports or existing unassigned evidence as a side effect of this planning update. Cleanup must account for revisions and report dependencies and retain a discard reason without retaining the discarded content itself.

## Actual implementation

Working: adapters/test boundaries, permissions, common evidence, manual project routing and exact segments, project-specific analysis, model fallbacks, citation checks, assignments, human confirmation, versioned decisions and Markdown report export. Four fictional test accounts and two separate TEST projects have twelve assigned open findings.

Required next: capture-to-analysis orchestration, reliable full-conversation segmentation, validated project matches, long-input coverage, provenance-preserving disposal, the Sources/Project Reviews reorganization, review filtering and consolidated-document output. Current storage retains originals and unassigned evidence; the legacy Unknown Context page is still present. No automatic deletion occurred during this update.

Build and test the conversation-to-project boundary first: it controls which findings appear, which memory is consulted and which content may be discarded.
