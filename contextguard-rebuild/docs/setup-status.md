# Local setup status

Current UI/setup: run `start.bat` and use its printed address. An older process at 8027 is preserved; the updated app on this machine uses **http://127.0.0.1:8028** with the same local records. Project Reviews accepts uploads/notes without registration and creates matched reviews automatically. Sources handles connections and Vexa links. See [the current guide](conversation-workflow.md). The table below also records earlier provider/service setup evidence.

Checked after the user requested setup completion and a launcher update. This records configuration presence, not live service verification. No provider or source request was made for the setup checks.

| Item | State | What the user needs to do |
|---|---|---|
| Python 3.11.15 / local .venv | Installed | Nothing |
| Pinned application dependencies | Installed; pip check passed | Nothing |
| Local database / port 8027 | Ready; launcher starts the app | Keep the server terminal open |
| Local owner account | Created; the October 25 app health check confirms setup is complete | Sign in with your existing local account |
| Manual TXT/MD/PDF/DOCX / fictional demo | Ready | Upload/paste in Project Reviews or choose the fictional sample |
| Muse Wonder | Key, model and endpoint configured privately; **live-verified** with fictional documents (Oct 24, 2026) | Nothing; re-verify after prompt/model changes |
| Groq / NVIDIA fallbacks | Keys/models configured privately; **Groq live-verified independently**; **NVIDIA live-verified as fallback responder**, but as isolated primary it exceeded the 35s bounded timeout (≈80s probe, truncated output) | Treat NVIDIA as fallback-only within current bounds; expect Groq quota intermittency (8,000 tokens/min observed) |
| Vexa | **Local self-hosted stack configured and scope-validated** (Oct 25, 2026): existing local Vexa v012 gateway at `127.0.0.1:18056`, dedicated ContextGuard key with `bot`+`tx` scopes (bot status 200; transcript read authorized/404 for unknown meeting), deployment transcription points to the local CPU Whisper service on :8083. ContextGuard restarted and reports Vexa configured | Create a fictional test meeting, set `VEXA_TEST_PLATFORM`/`VEXA_TEST_MEETING_ID` in `.env` (or paste the meeting link in Sources), then Join → admit bot → talk → Stop → Fetch. No hosted key or payment is used |
| Slack | OAuth app or scoped local token not configured | Set up/authorize the Slack app and selected channel. DPAPI protect/decrypt round trip now passes in the normal Windows session (synthetic probe); a real OAuth token round trip is still untested |
| WhatsApp / Baileys | Manual/test import only | Use a selected chat text export; live pairing remains disabled |

The user authorized using the existing local model configuration during this setup. Only supported model settings/keys were migrated into this repository's ignored `.env`. Values were not printed, copied into documentation, committed or sent externally. No source database or previous app code was copied.

## Launcher behavior

Double-click `start.bat`. It checks supported Python, creates/preserves the local environment, checks pinned packages, creates `.env` only if absent, shows safe configuration status and waits for the local app before opening a browser. A second launch reuses this same workspace. An unrelated/older process occupying the port is reported; it is never terminated automatically.

Run `start.bat --check` for setup status only. Missing optional connectors do not prevent the fictional/manual workflow. No Node frontend build, Docker or connector service is required for that path. Vexa self-hosting and a future Baileys runtime are separate services, not silently installed.

The startup check does not test provider credentials, pair WhatsApp, join a meeting, read Slack messages or send document content. Live analysis still requires explicit in-app transfer consent.

The later explicitly requested real-model check (`start.bat --live-check`) first failed in a restricted sandboxed session (Windows denied outbound connections). Re-run in a normal user session, Muse Wonder and Groq verify independently and the controlled-failure fallback verifies via NVIDIA; NVIDIA-as-primary remains latency-bound. See docs/live-testing.md. Vexa account/key setup is complete; its selected authorized meeting and end-to-end transcript/report test remain outstanding. Slack still needs account configuration, and safe Baileys pairing remains unimplemented.

October 25 inspection: app health 200; Vexa bot status 200; selected nonexistent-meeting transcript request 404; 57 automated tests passed. The normal workspace has an owner account but no projects/reviews/Vexa evidence yet. The transcript 404 establishes no completed meeting or transcription result. Docker administration was unavailable to this inspection session, so container/STT health was not independently recertified; the gateway itself was reached successfully.
