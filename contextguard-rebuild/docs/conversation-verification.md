# Conversation-first verification — October 25, 2026

Latest refinement: 95 automated tests pass, including safe single-demo cleanup/idempotence and Vexa/Slack button/API flows. The browser suite now has eleven grouped journeys, with selected-project manual capture, minimal Team, correct Source requests, link retention and passcode clearing. These results supersede the older counts below. Real Vexa was unreachable in the latest read-only check; Slack is unconfigured; no real meeting or live WhatsApp session is claimed. See sources-guide.md.


Story: a user captures authorized conversation/documents, receives project-specific evidence-linked reviews, filters them, records and confirms a resolution, and downloads updated project context. Only the rebuild was changed.

## Latest processing/network follow-up - October 26, 2026

42 targeted Python tests, six Node progress tests and four grouped isolated progress-browser checks passed. The previous UI pass also completed all 12 existing browser journeys. These checks use fictional providers, not external accounts. The latest real six-document sample attempt failed at 0/82 passages because outbound connections were denied; an earlier attempt failed citation validation after analysis. Neither is a passed review. Per-attempt timing and a normal-launch offline-account guard are implemented. See [processing details](processing-ui.md) and [recovery](windows-network-recovery.md). The following evidence table records earlier controlled verification.

## Evidence

| Boundary | Result | Evidence |
|---|---|---|
| Project setup | Passed | Browser creates Orchid using project controls above the cards; the selector is absent from the sidebar; existing projects without these fields remain compatible |
| Sources screen | Passed | No registration form or Unknown Context tab; explicit Vexa meeting-link Join/Stop/Fetch, Slack connection controls and truthful WhatsApp manual-only status |
| Capture → API | Passed | Real multi-file upload and pasted conversation submitted through the browser; sources created internally |
| Complete input → routes | Passed, controlled | Every non-whitespace character covered; all unit IDs returned exactly once; explicit scope/source mappings, changed profiles and revoked access enforced |
| Routing → project reviews | Passed, controlled | One fictional mixed conversation produces separate Orchid/Cedar reviews; chatter is removed from active input/evidence, not copied into either project |
| Provider failure | Passed | Controlled browser error retains input, exposes retry and creates no invented findings; duplicate resubmission reuses the retained job |
| Revisions/deletions | Passed | Observed source updates retire removed active passages and invalidate old reports while preserving confirmed decision history |
| Citations | Passed | Displayed/generated references point to exact retained project passages; invalid references fail processing and preserve raw input |
| Roles and confirmation | Passed | Browser proves assigned reviewer can respond but cannot assign/confirm even with a known response; backend independently enforces permissions |
| Review filters | Passed | Project/source/date/status API filters; browser exercises project/date filtering, clearing and reload |
| Output | Passed | Actual browser Word/report downloads; downloaded Word parsed with python-docx and confirmed answer/open questions/source evidence verified; Markdown document endpoint tested |
| Responsive UI | Passed | Desktop and 390px library/Sources screenshots inspected; no horizontal overflow or browser JavaScript errors; keyboard drawer close restores focus |
| Launcher | Passed | Actual `start.bat` detects the preserved older API at 8027 and starts/reuses the current instance at 8028 with existing records |

The complete automated suite passed **89 tests**. The only warning is the existing nonfailing Starlette TestClient/httpx deprecation. New intake/URL checks independently passed 26 tests after final parser repairs. `node --check` passed for all three UI modules. Repository/history credential scanning and `git diff --check` passed. No normal user data or existing decisions were deleted/reset by verification.

The browser runner records **nine grouped passing journeys** with zero page errors in ignored `artifacts/conversation-browser/results.json`, with desktop/mobile/role screenshots and actual downloads. `scripts/browser_server.py` always creates a fresh ignored database and uses a provider that refuses external calls; fictional routing/analysis is explicitly selected for success tests. This cannot certify real model quality or real connector accounts.

All four existing `test.*` accounts also signed in to the updated normal instance at 8028 and opened their saved assigned findings with the current role-aware UI, without changing answers/decisions. The older 8027 address displays guidance to run the updated launcher. Actual `start.bat --check` and repeat launch detect/reuse 8028; the existing database and original project are preserved.

## Live boundary

`scripts/verify_conversation.py --live` was attempted with only its built-in fictional two-project conversation, isolated accounts/database and configured provider keys. Muse Wonder, Groq and NVIDIA were all denied outbound access by local Windows/network permissions before an HTTP response. The run failed safely with no routing/reviews and retained its fictional input. The redacted result is in ignored `artifacts/conversation-live/b0689e307f6741a6806d3326fa3e2bba/results.json`.

Earlier Muse Wonder/Groq and controlled-NVIDIA fallback successes are historical provider-only evidence; they do not prove this new matching prompt works live. Real consented Vexa meeting → transcript → project report and real Slack authorization/pull remain pending. Experimental Baileys pairing/selected-text code has since been implemented, but a real phone connection remains unverified. See the WhatsApp pairing follow-up below; manual export remains the fallback.

## Remaining limits

Processing visibility follow-up (October 26, 2026): four Node checks, four grouped delayed-provider browser checks using the six Synora documents, and all 12 existing grouped browser journeys passed. Screenshots cover immediate upload, analysis and 390px layout. The user's real sample run was inspected read-only and still failed citation validation; no live review success is claimed. See processing-ui.md.

- Semantic matching may be wrong despite valid coverage/citations. Longer inputs use ordered batches with neighboring context, not an unlimited context window. Character/unit/provider bounds reject oversized selections without truncation.
- Unmatched/uncertain input is removed from active records only after successful processing; failed staging and older history remain. SQLite journals/backups and external providers prevent a secure-erasure claim.
- Vexa fetching and selected Slack imports are explicit; no unattended completion watcher or Events ingestion is implemented.
- Slack channel selection currently lists public channels the bot has joined. Older encoded Teams links are rejected; numeric `/meet/{id}` links are supported.
- Word output is a deterministic consolidation of confirmed decisions, unresolved questions and retained original evidence; it does not invent facts or silently rewrite original uploads.
- Final learner hands-on review remains open; automated checks are not recorded as personal learning participation.

## WhatsApp pairing follow-up

100 Python tests, four Node tests and 12 grouped browser journeys passed. Added admin/consent checks, selected-source isolation, source-backed review processing, QR UI/group selection/disconnect, pending-text event handling and encryption checks. Real stdio worker coverage uses fake socket/QR/key protection; npm installation and genuine DPAPI access were denied. No real account was paired. See whatsapp-live.md for precise live blockers and the remaining acceptance path.
