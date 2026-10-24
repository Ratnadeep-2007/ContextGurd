# Local setup status

Checked after the user requested setup completion and a launcher update. This records configuration presence, not live service verification. No provider or source request was made for the setup checks.

| Item | State | What the user needs to do |
|---|---|---|
| Python 3.11.15 / local .venv | Installed | Nothing |
| Pinned application dependencies | Installed; pip check passed | Nothing |
| Local database / port 8027 | Ready; launcher starts the app | Keep the server terminal open |
| Local owner account | First-use setup still required at check time | Open the app and choose a name/password |
| Manual TXT/MD/PDF/DOCX / fictional demo | Ready | Add a source or choose the fictional sample |
| Muse Wonder | Key, model and previously used endpoint configured privately | Verify a consented fictional live review; configuration is not proof of access |
| Groq / NVIDIA fallbacks | Keys/models configured privately | Verify actual account/model access separately |
| Vexa | No key/service connection configured | Supply a hosted/self-hosted Vexa key and an authorized meeting when needed |
| Slack | OAuth app or scoped local token not configured | Set up/authorize the Slack app and selected channel; protected OAuth storage still needs validation in the normal Windows session |
| WhatsApp / Baileys | Manual/test import only | Use a selected chat text export; live pairing remains disabled |

The user authorized using the existing local model configuration during this setup. Only supported model settings/keys were migrated into this repository's ignored `.env`. Values were not printed, copied into documentation, committed or sent externally. No source database or previous app code was copied.

## Launcher behavior

Double-click `start.bat`. It checks supported Python, creates/preserves the local environment, checks pinned packages, creates `.env` only if absent, shows safe configuration status and waits for the local app before opening a browser. A second launch reuses this same workspace. An unrelated/older process occupying the port is reported; it is never terminated automatically.

Run `start.bat --check` for setup status only. Missing optional connectors do not prevent the fictional/manual workflow. No Node frontend build, Docker or connector service is required for that path. Vexa self-hosting and a future Baileys runtime are separate services, not silently installed.

The startup check does not test provider credentials, pair WhatsApp, join a meeting, read Slack messages or send document content. Live analysis still requires explicit in-app transfer consent.
