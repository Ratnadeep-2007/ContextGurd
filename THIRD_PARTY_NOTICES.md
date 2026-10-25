# Third-party dependencies and references

This fresh implementation uses standard FastAPI, Starlette, Uvicorn, Pydantic, httpx, python-multipart, python-dotenv, pypdf, python-docx and pytest packages. Their respective upstream licenses apply; installing packages does not remove their notices. Playwright/Microsoft Edge are optional development verification tools, not copied application code.

The Devpost Learn Skill Pack is reused as local agent curriculum, excluded from application commits. See https://github.com/challengepost/learn-ai-basics for its own terms/notices.

Vexa, Slack and OpenAI-compatible provider endpoints are third-party service interfaces; the operator must have authorization and comply with their terms. Vexa's code/service is not bundled. Baileys' upstream MIT license and constraints were inspected, but its prerelease runtime is not bundled or installed and no live pairing is enabled. The adapter accepts a documented test/import envelope only. Primary sources are cited in docs/integration-research.md.

No Synora implementation or previous ContextGuard application code, schema, prompts or UI assets are included. Fictional sample text and test PDF content were authored for this fresh build.

## Locally bundled presentation resources

The user requested visual inspiration from the original ContextGuard interface. The new presentation code was independently written; the original application's React components, CSS and assets were not copied. DM Sans font files are standard third-party assets from `@fontsource/dm-sans` (SIL Open Font License); the bundled license is `web/assets/DM-Sans-LICENSE.txt`. Selected Lucide icon definitions are unchanged third-party library data from `lucide-react` 0.555.0 (ISC, with its Feather notices), bundled as `web/assets/icons.svg`; the full upstream notice is `web/assets/Lucide-LICENSE.txt`. Both libraries came from installed package resources, not the previous application's asset bundle. No external font/icon CDN is used.
