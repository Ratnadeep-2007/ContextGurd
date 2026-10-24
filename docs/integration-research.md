# Source integration research

Checked 24 October 2026 against first-party documentation and source. This is design research, not a record of working accounts or live integrations. No meeting was joined, WhatsApp device paired, Slack workspace connected, or customer content fetched for this research.

## Vexa

The current reference consolidates the old bots/transcripts pages into the [Meetings API](https://docs.vexa.ai/api/meetings). Send an explicitly authorized bot with `POST /bots`, `X-API-Key`, `platform`, `native_meeting_id` and a visible `bot_name`; platforms include `google_meet`, `teams`, and `zoom`. Set `recording_enabled:false` if recording is unnecessary. Read `GET /transcripts/{platform}/{native_meeting_id}`; stop with `DELETE /bots/{platform}/{native_meeting_id}`. Handle admission/status failure, `404`, duplicate-active `409`, and rate/concurrency refusal without inventing a transcript.

Preserve the complete returned transcript separately from routed segments. Current segments can contain `segment_id`, `speaker`, `text`, `start`/`end`, `absolute_start_time`/`absolute_end_time`, `completed`, `confidence` and `words`. Empty speaker means unattributed. Pending segments (`completed:false`) can be replaced by confirmations; stable source IDs and revisions must prevent duplicate evidence. Older examples use `start_time`/`end_time`, so normalize both variants explicitly. Confidence is transcription uncertainty, not factual reliability. Self-hosted transcription settings belong at Vexa; ContextGuard does not add Whisper.

**Boundary:** no Vexa deployment/account or meeting admission was tested. Hosted and self-hosted behavior must be verified against the deployment version before advertising live support. See also [custom STT configuration](https://docs.vexa.ai/how-to/custom-stt).

## Slack

Use the [official OAuth flow](https://docs.slack.dev/authentication/installing-with-oauth/): redirect to `https://slack.com/oauth/v2/authorize`, use a one-time session-bound expiring `state`, then exchange `code` at `oauth.v2.access`. Validate state before exchanging. Preserve the returned workspace/team, actor, token type and granted scopes. User tokens, when requested, are nested under `authed_user`; do not confuse them with top-level bot tokens. Store secrets locally outside source control, redact failures, and support disconnect/revocation. A granted OAuth token does not constitute approval to ingest every accessible channel.

Start with `channels:read` plus `channels:history` for selected public channels. Add `groups:read` and `groups:history` only when private-channel support is requested and permitted. DMs, message sending, broad search and profile-read scopes are unnecessary for this POC. Channel/token membership and endpoint permissions still apply. [Conversation listing scopes](https://docs.slack.dev/reference/methods/conversations.list/), [history scopes](https://docs.slack.dev/reference/methods/conversations.history/).

Fetch only approved channels/date ranges with `conversations.history`, paginate by cursor, and fetch specifically selected threads with `conversations.replies(channel,ts)`. Preserve team/channel IDs, exact message `ts`, `thread_ts`, `user`/bot identity, original text and edit metadata. Thread retrieval returns a parent plus replies; deduplicate by message identity, not text. Token compatibility must be verified on the actual workspace; surface `missing_scope`, `not_in_channel`, `token_revoked` and thread errors instead of claiming full coverage. [History](https://docs.slack.dev/reference/methods/conversations.history/), [threads](https://docs.slack.dev/reference/methods/conversations.replies/).

Resolve original links through [`chat.getPermalink`](https://docs.slack.dev/reference/methods/chat.getPermalink/). Preserve IDs/location if a permalink cannot be fetched; do not fabricate a working external link.

Honor HTTP `429` and its `Retry-After`, with bounded retries and visible partial completion. Slack applies limits per API method/workspace/app, and current limits depend on the method; avoid hardcoding an old blanket one-request-per-minute claim. [Rate limits](https://docs.slack.dev/apis/web-api/rate-limits/).

For edits use the nested `message.ts` and `message` payload, preserving prior provenance/revision rather than treating the delivery timestamp as a new message. For deletion use `deleted_ts` and channel to invalidate current evidence; absence from one paginated history response is not proof of deletion. Mark dependent reports stale. [Changed messages](https://docs.slack.dev/reference/events/message/message_changed/), [deleted messages](https://docs.slack.dev/reference/events/message/message_deleted/). If receiving Events API callbacks, verify signature over the raw body and reject stale timestamps, then deduplicate `event_id`; localhost still needs an explicitly configured delivery mechanism. [Request verification](https://docs.slack.dev/authentication/verifying-requests-from-slack/).

**Boundary:** OAuth installation, token storage, permission behavior, live channel/thread retrieval, edits and deletions need a real authorized workspace test. Mock HTTP tests establish parsing/error contracts only. Polling cannot guarantee capture of deletions without validated Events delivery or explicit reconciliation.

## WhatsApp / Baileys

The inspected upstream [package manifest](https://github.com/WhiskeySockets/Baileys/blob/master/package.json) declares package name `baileys`, version `7.0.0-rc14`, ESM and Node `>=20`. This is a moving master prerelease, not proof of the latest stable registry release. Old examples import `@whiskeysockets/baileys`; choose and pin a verified release rather than mixing examples. Upstream is [MIT licensed](https://github.com/WhiskeySockets/Baileys/blob/master/LICENSE); retain its notice when distributing its code. MIT licensing does not grant WhatsApp service authorization.

Upstream explicitly disclaims affiliation/authorization by WhatsApp, warns of breaking changes, discourages bulk/automated messaging and stalkerware, and says the new guide is unfinished. [Current README](https://github.com/WhiskeySockets/Baileys/blob/master/.github/README.md). WhatsApp's [Terms of Service](https://www.whatsapp.com/legal/terms-of-service) impose acceptable-use restrictions; this research does not establish that a proposed deployment is authorized by WhatsApp.

The [legacy guide](https://github.com/WhiskeySockets/Baileys/blob/master/README.md) describes linked-device auth state, updating credentials/Signal keys, and `messages.upsert`. Its multi-file auth helper is an example and not a production-grade storage recommendation. Do not copy the guide's terminal QR logging, full-message console logging, automatic replies, or whole-history store into ContextGuard. Treat QR/pairing material and session files as secrets: no logs, source control, browser storage or unprotected HTTP exposure. Use an OS-protected per-user location and document Windows ACL requirements.

**Implementation recommendation:** keep live pairing disabled/isolated until dependencies, session protection, selected-chat filtering and authorized use are validated. Offer fictional Baileys-shaped test events plus explicitly selected manual text/export import. Label these as tests/imports, not a connected WhatsApp account. A future read-only sidecar must allowlist chat/group IDs before retaining content, ignore every other chat, avoid full-history sync and implement no send/reply/read-receipt endpoint. Preserve remote JID, participant identity, message ID, timestamp and reply context. Add explicit connect/disconnect and retention controls; transport access remains broader than the application's ingestion filter and must be disclosed.

## Shared pipeline checks

The selected Groq fallback `openai/gpt-oss-120b` is currently listed among [supported production models](https://console.groq.com/docs/models). Its account access remains unverified here; the adapter validates structured responses locally and never treats a model's output as verified truth. No model availability is inferred for Muse Wonder/NVIDIA without the user's configured endpoint/model.

All adapters should emit one evidence contract and pass authorization, workspace, source selection and deterministic routing gates before project memory access. Keep model suggestions separate from confirmed routing. Unknown evidence remains in an inbox. Store raw provenance and revisions, reject duplicate deliveries, invalidate stale citations on source edits/deletions, and preserve complete meeting originals when routing approved segments.

Live integration labels require the full authorized source → adapter → evidence → routing → report path to have actually run. No integration earns that label from this research alone.
