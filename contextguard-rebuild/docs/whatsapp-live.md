# Experimental read-only WhatsApp pairing

Implemented locally; **no real account has been paired or certified working**. Windows blocked npm downloads (`EACCES`) and the current-user DPAPI probe in the development session. The app fails closed rather than emitting a fake QR or writing plaintext session secrets.

## Setup and use

1. Use a normal local Windows session with Node.js 20+ installed. Run `setup-whatsapp.bat` from this rebuild. It installs exact direct pins `baileys@7.0.0-rc14` and `qrcode@1.5.4`, using an ignored local npm cache. Setup never links an account. Successful installation produces the dependency lockfile; no transitive lockfile or native Windows compatibility is claimed before installation succeeds.
2. Run this rebuild's `start.bat` and open the updated address. Sign in as Ratnadeep/admin. In Sources > WhatsApp, choose Refresh status.
3. Confirm authorization, then Pair / reconnect WhatsApp. On your phone choose WhatsApp > Settings > Linked devices > Link a device, and scan the displayed QR. It refreshes while pairing. Do not share or screenshot a genuine QR. No API key is needed.
4. Once connected, Load available groups retrieves group names/IDs, not message history. Choose only authorized groups, optionally enter a direct-chat phone number with country code or an exact chat ID, confirm permission, and Save selected chats. Hold Ctrl to select multiple entries. An empty selection clears buffered text and stops collection. Selection is not restored across app restarts; approve it again after reconnecting.
5. Leave ContextGuard running while selected new text arrives. Refresh status to see the waiting count. In Project Reviews, select Current project and open Process selected WhatsApp text. Explicitly authorize external model processing before submitting. Findings, clarification and confirmed decisions use the common project pipeline.
6. Disconnect & forget attempts linked-device logout and deletes local session files. If the network is unavailable, revoke the device manually in your phone's Linked devices. Closing the app stops collection and preserves only the encrypted session for explicit reconnect.

## Connection and privacy boundary

- Baileys is an **unofficial** WhatsApp Web library, under MIT; its maintainers require responsible use and discourage spam/surveillance. This experimental feature is not a WhatsApp-supported or production-certified integration. See [upstream disclaimer/license](https://github.com/WhiskeySockets/Baileys#disclaimer) and [versioned research](baileys-research.md).
- Linking gives device-level account access even though ContextGuard filters retention to selected chats. Selecting groups accesses their metadata. Incoming protocol traffic is handled by Baileys; do not interpret the selection control as WhatsApp granting a channel-scoped token.
- No socket is opened at normal app startup or by a status check. Only an authorized admin's Pair action opens it. The worker uses private stdio, not a public bridge port. QR/status/selection/capture/disconnect endpoints require the admin session and standard local-origin protections.
- Full-history sync and online-on-connect are disabled. There is no application send/reply, media download, read-receipt, bulk-message or autonomous review-processing endpoint.
- Sessions are stored only under ignored `data/whatsapp/<workspace>/`: AES-256-GCM ciphertext and a Windows-current-user DPAPI-wrapped random vault key. Directory ACLs restrict access to the current user. There is no plaintext fallback. Session data must not be committed, shared or uploaded in support logs.
- Pending selected text stays in memory until explicitly queued. The normal durable intake then owns retry/success cleanup. Model consent sends selected text and eligible project context to external model providers. Retained quoted evidence and confirmed decisions are stored in the local project database. Disconnect does not delete earlier reviews.

## Coverage and limits

Only plain text received after selecting chats is captured. Media, captions, view-once content, reactions and past history are excluded. A single app may approve up to 20 chats, with at most 300 pending text messages / 60,000 characters. Buffer overflow blocks processing rather than presenting a silently truncated batch; clear selection and collect a smaller batch or use a manual export. Restarting loses unqueued in-memory text.

Pending duplicate events replace the same chat/message ID; edits update pending text and deletions remove it. Acknowledgment clears only queued revisions, preserving later edits. **Changes/deletions after capture do not automatically revise an earlier review or saved decision**; those records remain source snapshots. Refresh/reimport relevant evidence for a new review. Direct-chat phone/linked-identity aliases are not guessed; if an ID does not receive messages, use the exact supported chat ID or manual export.

Transient disconnect retries are bounded. Logout, invalid/replaced sessions and forbidden connections stop collection and clear selection. Use Disconnect & forget, then pair again if necessary. Keep manual export available when Baileys or native dependencies cannot operate reliably.

## What was tested

- Admin/consent checks, denial for reviewers, unauthorized-chat rejection, QR-image endpoint and selected capture through analysis to cited review: controlled local API tests.
- Real private Python→Node stdio worker and AES encrypted file lifecycle with a **fake socket, fake QR encoder and test-only key protector**. The actual DPAPI denial was observed separately; a regression test verifies failure blocks pairing. No test substitute is enabled in the normal app.
- Node unit tests: selection, deduplication, pending edits/deletes, bounded buffers, revision-safe acknowledgment and authenticated encryption/tamper rejection.
- Browser controls use controlled QR/status/group responses, not a linked phone.

Remaining live work: install and import the real pinned dependencies, verify Windows DPAPI in the normal user session, scan a genuine QR, select an authorized chat, receive a real test message, process with explicit model consent, verify citation/assignment, then disconnect and reconnect. No source integration success is claimed until that path passes.
