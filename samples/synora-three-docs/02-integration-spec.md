# Synora pilot — integration specification v2

Synthetic test scenario. These documents are fictional and do not change the real Synora project.

Document date: October 21, 2026. Version: 2. This specification replaces the connector appendix v1 dated October 5, 2026.

## Current Google Meet behavior

Process a native Google Meet transcript after the meeting has ended and the completed transcript is available. Preserve speaker and timestamp references before routing its evidence to projects.

The live-caption poller described in connector appendix v1 is retired. Do not build new work against its live-caption endpoint. Use the completed-transcript synchronization path in this v2 specification.

## WhatsApp dependency

The WhatsApp bridge is not connected in the test environment. The client’s project-group authorization is still pending. Priya owns bridge setup, but client authorization has no confirmed completion date in the supplied records.

Until both connection and authorization are complete, keep WhatsApp ingestion work pending. Dashboard and source-preview work can continue.

## Evidence and project memory

Keep original evidence and historical user clarifications distinct. Project recall must not retrieve a different project’s decisions. A remembered answer must be reconfirmed when a new document proposes a different value.

Excalidraw remains generated, read-only output. Direct canvas edits are not a pilot input.

## Approval and operating costs

Security approval is required before external pilot invitations. This specification contains no approval attachment or named security approver.

The pilot sends excerpts to configured AI providers. Provider quotas, expected request volume, and a monthly cost allowance must be checked before committing the operating budget. No quota or cost assessment is included in this specification.
