# Conversation-first workflow

Implemented in the rebuild only. The previous manual source-registration page and separate Unknown Context tab are removed. This document supersedes older setup journeys that required source IDs.

## Try it locally

Run `start.bat` in this folder and open the URL it prints. The preferred address is `http://127.0.0.1:8027`; if an older rebuild is already running, the launcher preserves it and chooses/reuses an updated instance on ports 8028–8035. On this machine the updated app is at **http://127.0.0.1:8028**. Existing accounts, projects and decisions use the same local database. Use that active port when configuring a Slack OAuth callback.

1. Sign in. Open **Create a project** above the cards in **Project Reviews**. Add its name, description and default review goal. Describe terms and milestones people actually use in conversation.
2. In **Project Reviews**, choose files or paste a conversation. Up to eight TXT/MD/PDF/DOCX files are supported, with a 4 MB per-file, 6 MB request, 30 PDF-page and 60,000 extracted-character batch limit. Limits produce errors rather than silently dropping text. Use unique filenames within one batch.
3. Select **Current project** before adding documents or pasted text. The selected project scopes both processing and the visible review list; the upload panel is disabled when no project is selected. Unrelated text is still omitted rather than forced into that project.
4. Confirm authorization and model consent, or enable fictional test analysis under **Review options**. Those options also contain the goal and member-sharing setting. Click **Process content**; source records are created internally.
5. **Recent processing** shows coverage and generated reviews. Failures retain the complete input and offer **Retry retained input**. A successful input with no project matches creates no review or memory entry.
6. Use **Current project** above the cards to select a project; use the Reviews filters for source, creation date and status. Open a review and compare findings with the exact source passages. Review creation dates and original source dates are distinct.
7. The review owner confirms an assignee. The accountable person answers with a cited statement or **Other**. A response is saved immediately but stays unresolved until an authorized project/decision owner confirms it. Unknown answers remain unresolved. Topic responsibility does not itself grant decision authority.
8. **Download report** exports the Context Gap Report. **Download updated document** exports Word with confirmed current decisions, unresolved questions and original evidence. Markdown is also available from `/api/reviews/{id}/document?format=md`. The original uploaded file is not overwritten.

The **Try fictional sample** button reuses an existing demo when available. This machine has one fictional Synora review with three sample documents; it opens without external model calls. Existing TEST project accounts and private credentials remain described in [test-users.md](test-users.md).

## Sources page

- **Vexa:** meeting link/passcode, explicit authorization, Join, Stop and Fetch-and-process controls. Joining is requested, not presumed admitted; connection checks report bot API reachability and observed status. Google Meet standard-code links, Zoom numeric links and Teams `/meet/{numeric-id}` links are parsed locally. Older encoded Teams invite URLs are rejected with guidance. Passcodes are sent only to the configured Vexa boundary and are not retained in ContextGuard. Transcript fetching is explicit; no unattended meeting watcher is claimed.
- **Slack:** official OAuth, authentication check and local disconnect. Selected public channels the bot has joined, optional threads and dates are imported from Project Reviews. Partial bounded pulls are rejected and require a smaller selection. No workspace-wide message capture or sending exists. OAuth client/live workspace setup is still required.
- **WhatsApp:** truthful manual-import status. Upload an authorized text export in Project Reviews. Baileys-shaped test import remains available at the isolated legacy API; live pairing/runtime is not implemented.
- **Manual input:** uploads and notes live only in Project Reviews. No registration panel or user-entered internal source ID is needed.

## Processing and retention

The complete input is staged privately. Sentences are split into exact offset-based units; every non-whitespace character must be covered. Ordered batches of up to 45 units/14,000 text characters, with neighboring context, are classified against authorized project profiles. All unit IDs must occur exactly once in the model result. Inaccessible IDs, duplicate/missing units, source-map violations and changed profiles are rejected before memory lookup. The model remains fallible at semantic project matching; validation establishes permission, coverage and provenance rather than factual truth.

Matched units retain exact text, author, date, location, original source/item ID and offsets under project-specific source grants. Each matched project is reviewed against its available evidence and confirmed decisions. Revisions and observed deletion events retire outdated active passages and make affected reports stale, without overwriting prior decisions. Identical uploads reuse their intake; changed files remain distinct source snapshots. A filename alone is not treated as proof that one document supersedes another.

Only after every generated review passes provider/schema/citation checks is the pending raw input cleared. Unmatched/uncertain units are not retained in active input/evidence, do not produce findings and never access project memory. Counts remain for coverage. No source-service messages are deleted. Historical reviews, decisions and old legacy records are preserved. SQLite/WAL/backups and external provider retention mean this is logical removal from active app records, not guaranteed secure disk erasure.

Live processing uses Muse Wonder, then configured Groq/NVIDIA fallbacks. The complete staged conversation and eligible project descriptions leave the computer only with model consent; project decisions are sent only after routing. A provider failure produces no fictional fallback. The new full-pipeline live check was attempted with fictional text and was blocked by local Windows outbound permissions on this agent session; prior provider-only successes do not certify this new prompt.

## Verification

Automated tests cover mixed projects, explicit/mapped/unauthorized routes, coverage, omission/duplicate rejection, disposal, retained-input retry, source revision/deletion, role authority, exact citations, report filtering, meeting URL parsing/passcode privacy and Word/Markdown exports. Browser verification exercises real uploads, two projects from one conversation, a confirmed answer, real downloads, filters, reload and 390px navigation. See [conversation verification](conversation-verification.md) for the final results and live boundaries.

Run `.\.venv\Scripts\python.exe scripts\test.py`. Use `node scripts/browser-conversation.mjs` against a fresh isolated database (defaults to port 8037). Run `.\.venv\Scripts\python.exe scripts\verify_conversation.py --live` only to explicitly send its built-in fictional conversation to configured models; it never reads the normal user/project database.

Current demo setup: one Synora project, Ratnadeep as the only admin/project owner, and four clearly labelled mock members. Team is a minimal role/responsibility table. See [the Sources guide](sources-guide.md) for current button behavior and live-service limits.
