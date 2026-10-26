# Baileys live read-only boundary research

Inspected October 25, 2026. These are implementation inputs, not evidence that a real WhatsApp account has been paired or that WhatsApp endorses this integration.

## Version and runtime

Upstream lists **v7.0.0-rc14** as its latest release and **v6.7.24** as its recent legacy release. The release history identifies a security fix in rc12 and legacy 6.7.22; avoid older pins. RC means a prerelease and should remain labelled experimental. See [upstream releases](https://github.com/WhiskeySockets/Baileys/releases).

The pinned rc14 manifest names the package `baileys`, uses ESM, requires Node >=20, declares MIT licensing, and depends on `whatsapp-rust-bridge` 0.5.4. Verify the published package and Windows native dependency actually install before claiming local availability. Use an exact package version and lockfile; do not depend on moving master or mix examples for the older scoped package without checking them. See [rc14 package manifest](https://github.com/WhiskeySockets/Baileys/blob/v7.0.0-rc14/package.json).

## Connection and credentials

The official example creates a socket using `makeWASocket`, loads `{state, saveCreds}` from `useMultiFileAuthState`, supplies the auth state, listens for `connection.update` containing `qr`, and saves on `creds.update`. A new QR can replace an earlier QR. Display it only to the authenticated connection owner; never log its text or save screenshots containing a live QR. `lastDisconnect.error.output.statusCode` is used in the example to detect logout. See [upstream example](https://github.com/WhiskeySockets/Baileys/blob/v7.0.0-rc14/Example/example.ts).

The multi-file helper stores the authentication and Signal keys in a directory as JSON. Its own source discourages general production use and recommends a proper database auth store. For this local prototype, isolate credentials below ignored private data, restrict filesystem access, and keep tokens, keys and raw errors out of source control and application logs. Linking grants device-level account access even when ContextGuard retains only selected chats. See [auth helper source](https://github.com/WhiskeySockets/Baileys/blob/v7.0.0-rc14/src/Utils/use-multi-file-auth-state.ts).

The enum defines restartRequired=515, loggedOut=401, connectionReplaced=440, forbidden=403, badSession=500, multideviceMismatch=411, connectionClosed=428 and connectionLost/timedOut=408. ContextGuard should recreate a socket after pairing's restartRequired, use bounded retry/backoff for transient loss, and stop with an actionable state on logout, replacement, forbidden or invalid sessions. This retry policy is our implementation decision, not a guarantee from the library. See [disconnect enum](https://github.com/WhiskeySockets/Baileys/blob/v7.0.0-rc14/src/Types/index.ts).

## Read-only selection and history

Set `syncFullHistory:false`, `shouldSyncHistoryMessage:()=>false` and `markOnlineOnConnect:false` explicitly. The rc14 defaults enable full history and online status; relying on defaults would violate ContextGuard's narrow selection behavior. `shouldIgnoreJid` is documented to prevent message events and decryption for ignored JIDs; implement it against the approved selection and independently filter again before retention. See [socket configuration](https://github.com/WhiskeySockets/Baileys/blob/v7.0.0-rc14/src/Types/Socket.ts) and [defaults](https://github.com/WhiskeySockets/Baileys/blob/v7.0.0-rc14/src/Defaults/index.ts).

The event contract exposes `messages.upsert` with a batch and notify/append type, `messages.update`, `messages.delete`, `chats.upsert/update/delete`, `groups.upsert/update`, and optional history events. Preserve message and chat IDs, sender identity and timestamps; deduplicate deliveries. Edits/deletions require handling or an explicit limitation. Do not retain unselected message bodies while building a picker. With history disabled, advertise incoming messages from selection time, not complete past conversation retrieval. See [event contract](https://github.com/WhiskeySockets/Baileys/blob/v7.0.0-rc14/src/Types/Events.ts).

`groupFetchAllParticipating` returns group metadata and emits groups.update; this can discover group names/IDs without an application-level message history request. For direct chats, manual identifiers or observed minimal metadata may be needed when full history is disabled. Reading the metadata still accesses the linked account and must be disclosed. No send/reply/presence/read-receipt API should be exposed by the bridge. See [groups implementation](https://github.com/WhiskeySockets/Baileys/blob/v7.0.0-rc14/src/Socket/groups.ts).

## License and service constraints

Baileys states that it is unofficial and unaffiliated with WhatsApp, calls on users to respect WhatsApp terms, and discourages stalkerware, spam and bulk/automated messaging. Retain upstream MIT attribution when distributing it. Official status, guaranteed operation and compliance cannot be inferred from its MIT license. Keep manual import available and label live operation experimental. See [README disclaimer and license](https://github.com/WhiskeySockets/Baileys#disclaimer) and [license](https://github.com/WhiskeySockets/Baileys/blob/v7.0.0-rc14/LICENSE).

The old wiki URLs `/docs/intro` and `/docs/socket/connecting/` returned 404 during this inspection, so this note relies on version-pinned upstream source rather than assuming those pages remain valid.
