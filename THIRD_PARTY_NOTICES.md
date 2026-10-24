# Third-party components

ContextGuard is a new application; its use of libraries does not transfer ownership of those dependencies or change their licenses. Installed packages retain upstream license files. The frontend lockfile records exact package versions and integrity hashes; backend/requirements-tested.txt records the verified environment's direct package versions.

| Component | License / source |
|---|---|
| React / React DOM | MIT — https://github.com/facebook/react |
| Vite | MIT — https://github.com/vitejs/vite |
| TypeScript | Apache-2.0 — https://github.com/microsoft/TypeScript |
| Lucide | ISC — https://github.com/lucide-icons/lucide |
| DM Sans / Manrope fonts | SIL Open Font License 1.1; bundled via @fontsource — https://fontsource.org/ |
| FastAPI | MIT — https://github.com/fastapi/fastapi |
| Starlette | BSD-3-Clause — https://github.com/encode/starlette |
| Pydantic | MIT — https://github.com/pydantic/pydantic |
| Uvicorn | BSD-3-Clause — https://github.com/encode/uvicorn |
| HTTPX | BSD-3-Clause — https://github.com/encode/httpx |
| pypdf | BSD-3-Clause — https://github.com/py-pdf/pypdf |
| python-docx | MIT — https://github.com/python-openxml/python-docx |
| python-multipart / python-dotenv | Apache-2.0 / BSD-3-Clause — upstream installed distributions |
| pytest | MIT — https://github.com/pytest-dev/pytest |
| Playwright | Apache-2.0 — https://github.com/microsoft/playwright |
| SQLite | Public-domain dedication — https://sqlite.org/copyright.html |
| Devpost Learn Skill Pack | External workflow reference, cloned in ignored tools directory — https://github.com/challengepost/learn-ai-basics |

The evidence map is native HTML/CSS over validated records; React Flow, Docling, LangGraph, LiteLLM and PyMuPDF were researched but are not shipped dependencies. Mem0 OSS has a REST integration in `backend/app/project_memory.py`; the SDK, service runtime and model weights are not bundled. An independently operated Mem0 service retains its upstream Apache-2.0 license and dependency/provider terms: https://github.com/mem0ai/mem0.

Meta Model API, Groq, and NVIDIA-hosted NIM are external services governed by their own provider/model terms. A model hosted by a provider is not automatically open-source software. No model weights are bundled.

Font license texts and frontend production dependency license texts are copied into `licenses/` for distribution. Preserve these notices when redistributing builds. Review transitive dependencies and API terms for your distribution; this list is not legal advice or a complete transitive-license audit.
