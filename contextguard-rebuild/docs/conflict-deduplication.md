# Consolidated findings and clean manual retesting

## Behavior

Models are asked for one finding per underlying decision/gap, with a stable issue_key reused across analysis batches. Code validates each incoming citation before consolidation. Same issue keys or normalized titles consolidate only within compatible scope/version/period/milestone boundaries; conservative title/question similarity additionally requires overlapping evidence. Verified facts stay separate from issues. Consolidation retains exact source passages, decision references, highest priority, uncertainty and related clarification questions. Different versions and different issue keys/topics remain separate in regression tests.

An unchanged successful review is reused using a signature of owner, project, goal, selected sources, evidence fingerprints, date range, mode and visible project memory. A failed intake retry replaces its own project review record rather than creating another card. A review with human responses cannot be overwritten by retry. Invalid model citations make the review failed and retain input; partial results cannot be confirmed as a completed review.

This is bounded duplicate prevention, not a guarantee of perfect semantic equivalence. A model can still choose inconsistent issue keys or miss a conflict. Distinct reviews for changed sources/goals/decisions remain legitimate; this is not a project-wide merge of every historical ticket.

## Manual reset

The requested reset removes captured sources, source events, evidence, routing mappings, intakes, reviews and decision memory. Users, sessions, projects/members/responsibilities, model configuration, connection settings and on-disk sample files are preserved. No new backup of the erased test content is created.

Run from the rebuild folder after processing has finished:

```powershell
.\.venv\Scripts\python.exe scripts/reset_test_content.py --apply
```

If the server was explicitly stopped during processing, verify it is stopped, then use --apply --server-stopped to clear interrupted job records. Do not use that flag while a server is still processing. Close/restart the normal server before the retest so Python loads the deduplication changes. Do not launch the normal server from the Codex offline account.

## Verification and current state

The full Python suite passed after the main implementation; eight focused consolidation/reset tests passed after the final reset safeguard additions. All 12 grouped isolated browser journeys passed with no page errors. One old batching assertion required exactly two source documents; it now requires at least two because a consolidated conflict correctly retains additional supporting documents.

The requested live database reset completed after both processing jobs reached failed status. The transactional reset removed 697 evidence records, 2 intakes, 5 reviews, 31 sources and 99 source events. Verification found no remaining reviews, sources, evidence, routing mappings, intakes or decisions; 5 users, 1 project, sessions and 2 connection-check records remain. Sample files and local settings are preserved. Restart the normal server before retesting so it loads the deduplication changes. Live model quality is not certified by these tests.

For a clean Synora test, upload only samples/synora-all-sources/01 through 06 together. Do not upload README, verification.json, or the transcript answer key. Expect five grouped issue families: pilot date, Atlas-edit evidence, memory approval, routing policy and missing owners/approval. Proposals remain unapproved; the last family is a gap, not a contradiction.
