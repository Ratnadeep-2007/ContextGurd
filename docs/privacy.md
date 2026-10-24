# Data, authorization and external services

## Local records
The app binds to 127.0.0.1:8027. Passwords are PBKDF2 hashes; opaque sessions expire after eight hours. Workspace, project and source grants are checked separately. These application roles do not prevent a Windows administrator or a person with access to your account/disk from reading the database. SQLite source/decision records are not encrypted at rest. Use Windows account controls and disk encryption, and do not expose this development server publicly.

The database preserves original selected text imports, historical passages, responses and decision provenance. Deleting/replacing a source passage does not erase history. There is no production retention/deletion management UI yet; choose fictional data for demos and manage local records deliberately. Test databases and screenshots stay under ignored `artifacts/`.

## Explicit external transfers
- Live model analysis sends the goal, selected routed evidence and visible prior project decisions to the configured provider, with fallback providers attempted on failure. The consent checkbox covers this provider chain. No fixture is substituted after failure.
- The model-routing button explicitly sends just that unknown passage and accessible project names; it does not send project decisions and cannot confirm a route.
- Vexa join contacts the configured service and asks a visible bot to join. The operator must have authorization and appropriate participant consent. A host may need to admit it. Fetch consumes Vexa's transcript, not local audio/STT. Recording is disabled in the join request. Stop is explicit.
- Slack OAuth and selected pulls contact Slack. Tokens grant API access; they do not approve every channel. Users still register a selected source and confirm processing. The app requests public-channel read/history scopes only; private channels require separately approved minimum scopes. No send or broad search scopes.
- WhatsApp has no live connection in this build. Baileys is unofficial and live pairing is disabled. Test event import filters the selected chat before retaining data. Manual export import is available.

## Credentials
Only the fresh repository's `.env` is loaded. At the user's request to finish local setup, supported model settings/keys were migrated privately from the earlier project's configuration into the ignored new `.env`; no source content, database or connector session was copied, and no provider request was made. The application/launcher does not automatically discover or import old credentials. `.env`, local databases, artifacts and the learner profile are ignored by Git. A secret-free `.env.example` lists settings. Slack OAuth tokens use Windows current-user DPAPI; failure refuses persistence. Test code uses a controlled protector for the OAuth wiring test because this session cannot use DPAPI. A protected-token round trip is not claimed. An environment token is an explicit local alternative, with `SLACK_TEAM_ID` checked against `auth.test`.

Access logging is disabled in the launcher so OAuth codes and query strings are not recorded. Provider failures do not echo response bodies, keys or source text. Avoid enabling debug/access logs. Local Slack disconnect removes/disables local access; revoke the installation in Slack settings to invalidate the external token. Source-grant revocation blocks subsequent report/memory access; a previously downloaded report is outside app access controls.

## Coverage limits
Citation verification proves an exact passage exists in selected evidence; it does not prove that statement is true or that all relevant evidence was selected. Comparison metadata catches explicit different versions/milestones, while interpreting unlabeled text remains fallible. Partial or failed parsing and truncated connector responses prevent an unqualified Ready status. No numerical readiness score is generated.
