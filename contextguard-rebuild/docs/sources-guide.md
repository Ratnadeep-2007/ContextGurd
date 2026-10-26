# Sources: controls and current setup

Use Sources as **Ratnadeep**, the workspace admin. Mock reviewers/decision owners do not configure external connections. No button joins a meeting or reads a conversation without the explicit source action and consent.

## Vexa meetings

1. Start Docker Desktop and the existing self-hosted Vexa stack, if they are not already running. The configured local gateway must be reachable.
2. Click **Check Vexa connection**. Connected means the bot API authenticated; it does not mean a bot has joined a meeting.
3. Paste your own meeting link and an optional passcode. Confirm participant authorization, then click **Join meeting**. The host may need to admit the bot.
4. Click **Stop bot** when finished. The link stays selected; passcodes are cleared after an operation and are not stored.
5. Enable model processing and click **Fetch and process transcript** once Vexa has the transcript. ContextGuard then creates matched project reviews. Review them in Project Reviews.

Current live result: the local Vexa gateway could not be reached during verification. Docker control was unavailable in this session and the expected daemon pipe was not found. No real meeting was joined/stopped/fetched. The configured key was not printed or changed. Start the existing service and retry Check; a real authorized meeting is still needed for full live verification.

Verified with controlled responses: connection success/failure feedback, correct Join/Stop/Fetch payloads, consent, link retention, passcode clearing, transcript normalization, project processing and citation preservation. A failed check now shows Connection failed instead of leaving a stale success badge.

## Slack

Current state: neither OAuth settings nor a scoped local token/workspace ID is configured. Connect cannot authorize a real account until one setup path is completed.

For local testing, install a Slack app with the required read scopes in your authorized workspace. Configure `SLACK_BOT_TOKEN` and `SLACK_TEAM_ID` privately in this rebuild's `.env`, restart the app, then click **Connect Slack**. In this mode the button verifies the local token and workspace. Do not paste credentials into chat or source files. Public channel reads use `channels:read` and `channels:history`; invite the app only to channels you are authorized to process.

Alternatively configure `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET` and an approved `SLACK_REDIRECT_URI` to use the OAuth button. Slack's standard OAuth documentation requires an HTTPS redirect; do not assume the placeholder HTTP localhost callback is accepted. See [Slack OAuth installation](https://docs.slack.dev/authentication/installing-with-oauth/) for the approved setup. Exposing the local application or configuring a tunnel was not performed here.

After connection, click **Check connection**. In **Project Reviews**, open **Import a selected Slack conversation**, load authorized channels and select the channel/thread/dates. **Disconnect locally** disables ContextGuard access; it does not revoke the Slack token. Reconnect validates the configured local token again or starts OAuth, as appropriate.

Verified with controlled responses: authentication, workspace matching, joined-channel filtering, selected import/processing, local disconnect/reconnect and missing-setup errors. Real Slack installation/token access remains unverified.

## WhatsApp and documents

For experimental live reading, run `setup-whatsapp.bat` once. In Sources, refresh WhatsApp status, authorize linking and choose Pair / reconnect. Scan the QR from WhatsApp > Linked devices. Load available group names/IDs, explicitly select authorized chats, confirm permission and save. A direct-chat phone number or exact chat ID may also be entered. Then select the project in Project Reviews and use Process selected WhatsApp text. Only new text received after selection is collected; no full historical conversation is downloaded. Disconnect & forget deletes the local session; check/revoke the device on your phone too. See [full setup, privacy and limitations](whatsapp-live.md).

Current live blockers: Windows denied npm network access and DPAPI protection in this execution session. No genuine QR/account pairing was completed. The UI reports Setup required until dependencies exist; credential-protection failure refuses pairing.

**Import a chat export** remains the fallback: Project Reviews opens in WhatsApp export mode. Select the project, upload an authorized TXT export and process it. No messages are sent.

**Add project context** opens normal document/text mode. New uploads and pasted notes are restricted to **Current project**. Select a project first; selecting All projects is for browsing, not manual ingestion.

## Verification record

The current browser checks cover every meeting button, Vexa check, missing Slack setup and WhatsApp navigation with explicitly controlled network responses. Backend tests independently exercise positive Vexa transcript processing and Slack read/disconnect/reconnect, including failure states. This proves wiring and validation; it is not live connector certification. See ignored `artifacts/source-control-live-check.json` for the actual configuration/reachability result.
