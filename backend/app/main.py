from __future__ import annotations

import os
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
VERSION = "1.1.0"
load_dotenv(ROOT / ".env")

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import Field

from .ingestion import MAX_BYTES, parse_source, parse_source_isolated
from .providers import configured
from .project_memory import ProjectMemory, decision_sources, digest
from .sample import sample_case
from .schemas import Case, Criterion, Model, PriorDecision, Resolution, Run, default_criteria, now
from .store import ConflictError, Store
from .workflow import analyze, brief, clarification_choices, clarification_options, fingerprint


class CreateCase(Model):
    title: str = Field(default="Untitled review", min_length=1, max_length=120)
    goal: str = Field(default="Are we ready to start development?", min_length=5, max_length=1000)
    scope: str = Field(default="", max_length=2000)
    project_id: str | None = Field(default=None, max_length=64)


class CreateProject(Model):
    name: str = Field(min_length=1, max_length=100)


class UpdateCase(CreateCase):
    version: int
    allow_fallback: bool = True


class TextSource(Model):
    name: str = Field(min_length=1, max_length=180)
    text: str = Field(min_length=1, max_length=60000)
    version: int


class CriteriaInput(Model):
    criteria: list[Criterion] = Field(min_length=1, max_length=8)
    version: int


class ResolutionInput(Model):
    finding_id: str
    action: str
    answer: str = Field(default="", max_length=3000)
    owner: str = Field(default="", max_length=120)
    option_text: str = Field(default="", max_length=3000)
    choice_id: str = Field(default='', max_length=80)
    version: int


class VersionInput(Model):
    version: int


def create_app(db_path: str | None = None, memory_index=None, serve_frontend=True) -> FastAPI:
    store = Store(db_path)
    memory = ProjectMemory(store, memory_index)
    executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="contextguard")
    @asynccontextmanager
    async def lifespan(app):
        memory.schedule()
        yield
        executor.shutdown(wait=True, cancel_futures=True)
        memory.close()
    app = FastAPI(title="ContextGuard", version=VERSION, description="Local, single-user evidence review. Not an approval system.", lifespan=lifespan)
    app.state.store = store
    app.state.memory = memory
    gate = threading.RLock()
    slots = threading.BoundedSemaphore(2)
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Content-Type"])

    @app.middleware("http")
    async def local_security(request: Request, call_next):
        # No remote bind or public multi-user claims; reject browser cross-origin writes.
        from fastapi.responses import JSONResponse
        host = request.headers.get("host", "").split(":")[0]
        origin = request.headers.get("origin", "")
        allowed_origins = {"http://localhost:5173", "http://127.0.0.1:5173", str(request.base_url).rstrip("/")}
        if host not in {"localhost", "127.0.0.1", "testserver"}:
            return JSONResponse({"detail": "This local app only accepts localhost requests."}, status_code=403)
        if request.method not in {"GET", "HEAD", "OPTIONS"} and origin and origin not in allowed_origins:
            return JSONResponse({"detail": "Cross-origin writes are not permitted."}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ConflictError)
    async def conflict_handler(request, exc):
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": str(exc)}, status_code=409)

    def get(case_id: str) -> Case:
        try:
            return store.get(case_id)
        except KeyError:
            raise HTTPException(404, "Review not found. It may have been deleted.")

    def editable(case_id, version, sample_ok=True):
        case = get(case_id)
        if case.version != version:
            raise ConflictError("This review changed. Refresh before saving again.")
        if case.run and case.run.status == "running":
            raise HTTPException(409, "Wait for this review to finish before changing its inputs.")
        if not sample_ok and case.mode == "sample":
            raise HTTPException(400, "Sample sources and goal are fixed for honest replay. Start a new review to use your own inputs.")
        return case

    def invalidate(case):
        case.report = None
        case.run = None
        case.changes = ["Inputs changed. Run the review again; previous answers will not be applied to changed sources or criteria."]

    def work(case_id, run_id):
        try:
            case = get(case_id)
            previous = case.report
            recalled = memory.recall(case)
            case.prior_decisions = []
            budget = 12000
            for entry in recalled['decisions']:
                size = len(json.dumps(entry, ensure_ascii=False))
                if size <= budget:
                    case.prior_decisions.append(PriorDecision.model_validate(entry))
                    budget -= size
            def progress(stage):
                with gate:
                    current = get(case_id)
                    if not current.run or current.run.id != run_id or current.run.status != "running":
                        raise ConflictError("Run superseded.")
                    current.run.stage = stage
                    store.save(current)
            report = analyze(case, progress)
            if len(case.prior_decisions) < len(recalled['decisions']):
                report.limitations.append('Some earlier project decisions were omitted from AI context because they exceed the memory budget. Inspect Earlier project decisions for the full recalled list.')
            with gate:
                current = get(case_id)
                if not current.run or current.run.id != run_id or current.run.status != "running":
                    return
                old = {f.id: f for f in previous.findings} if previous else {}
                changes = [f"{f.title}: {f.status.replace('_', ' ')}." for f in report.findings if f.id in old and (f.status, f.answer, f.owner) != (old[f.id].status, old[f.id].answer, old[f.id].owner)]
                if previous and not changes:
                    changes = ["Review refreshed. No finding status changed."]
                current.changes = changes
                current.report = report
                current.run.status = "completed"
                current.run.stage = "Review complete"
                current.run.finished_at = now()
                store.save(current)
                memory.schedule()
        except Exception as exc:
            with gate:
                try:
                    current = get(case_id)
                    if current.run and current.run.id == run_id and current.run.status == "running":
                        current.run.status = "failed"
                        current.run.stage = "Review stopped"
                        current.run.error = str(exc) if isinstance(exc, (ValueError, ConflictError)) or exc.__class__.__name__ == "ProviderError" else "The review could not finish. Your inputs are saved. Retry or inspect the server logs."
                        current.run.finished_at = now()
                        store.save(current)
                except HTTPException:
                    pass
        finally:
            slots.release()

    def start(case):
        if not slots.acquire(blocking=False):
            raise HTTPException(429, "Two reviews are already running. Wait for one to finish.")
        try:
            case.run = Run()
            store.save(case)
            memory.schedule()
            executor.submit(work, case.id, case.run.id)
            return case
        except Exception:
            slots.release()
            raise

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": VERSION}

    @app.get("/api/config")
    def config():
        providers = configured()
        return {"providers": [{"name": p.name, "model": p.model} for p in providers], "live_available": bool(providers), "local_only": True, "project_memory": memory.status(), "limits": {"sources": 8, "file_mb": 8, "characters": 90000, "pdf_pages": 30}}

    @app.get('/api/projects')
    def projects():
        return store.projects()

    @app.post('/api/projects', status_code=201)
    def create_project(data: CreateProject):
        if not data.name.strip():
            raise HTTPException(400, 'Enter a project name.')
        return store.create_project(data.name)

    def check_project(project_id):
        if project_id is not None:
            try:
                store.get_project(project_id)
            except KeyError:
                raise HTTPException(404, 'Project not found. Refresh the project list.')

    @app.get("/api/cases")
    def cases():
        return [{"id": c.id, "title": c.title, "project_id": c.project_id, "mode": c.mode, "updated_at": c.updated_at, "source_count": len(c.sources), "has_report": c.report is not None} for c in store.list()]

    @app.post("/api/cases", status_code=201)
    def create(data: CreateCase):
        check_project(data.project_id)
        return store.save(Case(**data.model_dump(), criteria=default_criteria()), create=True)

    @app.post("/api/cases/sample", status_code=201)
    def sample():
        return store.save(sample_case(), create=True)

    @app.get("/api/cases/{case_id}")
    def case_detail(case_id: str):
        case = get(case_id)
        if case.report:
            for finding in case.report.findings:
                finding.answer_options = clarification_options(finding, case.report.evidence)
                finding.clarification_choices = clarification_choices(finding, case.report.evidence)
        return case

    @app.get('/api/cases/{case_id}/memory')
    def recall_memory(case_id: str):
        return memory.recall(get(case_id))

    @app.post('/api/memory/retry', status_code=202)
    def retry_memory():
        memory.schedule()
        return memory.status()

    @app.put("/api/cases/{case_id}")
    def update(case_id: str, data: UpdateCase):
        with gate:
            case = editable(case_id, data.version, False)
            old = (case.goal, case.scope, case.project_id)
            if 'project_id' in data.model_fields_set:
                check_project(data.project_id)
                case.project_id = data.project_id
            case.title, case.goal, case.scope, case.allow_fallback = data.title, data.goal, data.scope, data.allow_fallback
            if old != (case.goal, case.scope, case.project_id):
                invalidate(case)
            saved = store.save(case)
            memory.schedule()
            return saved

    @app.delete("/api/cases/{case_id}")
    def delete_case(case_id: str, data: VersionInput):
        with gate:
            editable(case_id, data.version)
            store.delete(case_id)
            memory.schedule()
            return {"deleted": True}

    def add(case, source):
        if len(case.sources) >= 8:
            raise HTTPException(400, "Keep this review to eight sources. Remove a source before adding another.")
        if any(s.content_hash == source.content_hash for s in case.sources):
            raise HTTPException(400, "This source is already included. Duplicate content is not added twice.")
        count = sum(len(p.text) for s in case.sources for p in s.passages) + sum(len(p.text) for p in source.passages)
        if count > 90000:
            raise HTTPException(400, "This review exceeds 90,000 characters. Split it into a smaller decision.")
        case.sources.append(source)
        invalidate(case)
        saved = store.save(case)
        memory.schedule()
        return saved

    @app.post("/api/cases/{case_id}/sources/text")
    def add_text(case_id: str, data: TextSource):
        with gate:
            case = editable(case_id, data.version, False)
            name = data.name if data.name.lower().endswith((".txt", ".md")) else data.name + ".txt"
            return add(case, parse_source(name, data.text.encode("utf-8")))

    @app.post("/api/cases/{case_id}/sources/upload")
    async def upload(case_id: str, version: int, file: UploadFile):
        editable(case_id, version, False)
        raw = await file.read(MAX_BYTES + 1)
        await file.close()
        if len(raw) > MAX_BYTES:
            raise HTTPException(400, "This file exceeds 8 MB. Upload a smaller source.")
        # Parsing in a worker thread avoids blocking the API's event loop.
        from starlette.concurrency import run_in_threadpool
        source = await run_in_threadpool(parse_source_isolated, file.filename or "source", raw)
        with gate:
            return add(editable(case_id, version, False), source)

    @app.delete("/api/cases/{case_id}/sources/{source_id}")
    def remove_source(case_id: str, source_id: str, data: VersionInput):
        with gate:
            case = editable(case_id, data.version, False)
            if not any(s.id == source_id for s in case.sources):
                raise HTTPException(404, "Source not found.")
            case.sources = [s for s in case.sources if s.id != source_id]
            invalidate(case)
            saved = store.save(case)
            memory.schedule()
            return saved

    @app.put("/api/cases/{case_id}/criteria")
    def criteria(case_id: str, data: CriteriaInput):
        with gate:
            case = editable(case_id, data.version)
            # Only existing template criteria are editable; provenance cannot be forged through this UI.
            original = {c.id: c for c in case.criteria}
            if {c.id for c in data.criteria} != set(original) or len({c.id for c in data.criteria}) != len(data.criteria):
                raise HTTPException(400, "Keep the existing criterion IDs.")
            for c in data.criteria:
                if c.excluded and not c.exclusion_reason.strip():
                    raise HTTPException(400, "Add a reason for each excluded check.")
                original[c.id].excluded, original[c.id].exclusion_reason = c.excluded, c.exclusion_reason.strip()
            case.criteria = list(original.values())
            invalidate(case)
            saved = store.save(case)
            memory.schedule()
            return saved

    @app.post("/api/cases/{case_id}/analyze", status_code=202)
    def run(case_id: str, data: VersionInput):
        with gate:
            case = editable(case_id, data.version)
            if not any(s.status == "ready" for s in case.sources):
                raise HTTPException(400, "Add a readable source first.")
            if not any(not c.excluded for c in case.criteria):
                raise HTTPException(400, "Include at least one review criterion.")
            if case.mode == "live" and not configured():
                raise HTTPException(400, "Configure MODEL_API_KEY in the root .env, then restart the server. You can try the fictional sample now.")
            return start(case)

    @app.post("/api/cases/{case_id}/resolutions", status_code=202)
    def resolve(case_id: str, data: ResolutionInput):
        with gate:
            case = editable(case_id, data.version)
            finding = next((f for f in case.report.findings if f.id == data.finding_id), None) if case.report else None
            if not finding:
                raise HTTPException(404, "Finding not found. Run a current review first.")
            if data.action not in {"confirm", "dismiss", "unknown", "accept_risk"}:
                raise HTTPException(400, "Choose a supported resolution action.")
            choice = None
            if data.choice_id:
                choice = next((c for c in clarification_choices(finding, case.report.evidence) if c.id == data.choice_id), None)
                if not choice or choice.action != data.action:
                    raise HTTPException(400, 'This answer choice is unavailable or does not match its action. Refresh the review.')
                if data.option_text and (choice.kind != 'source' or choice.answer != data.option_text):
                    raise HTTPException(400, 'The source statement does not match the selected answer.')
            option = None
            option_text = choice.answer if choice and choice.kind == 'source' else data.option_text
            if option_text:
                if data.action != "confirm":
                    raise HTTPException(400, "Source options apply to an answer. Use a reason for the other actions.")
                option = next((x for x in clarification_options(finding, case.report.evidence) if x.text == option_text), None)
                if not option:
                    raise HTTPException(400, "This option is no longer available. Refresh the review before answering.")
            answer = choice.answer if choice else option.text if option else data.answer.strip()
            if data.action != "unknown" and not answer:
                raise HTTPException(400, "Add an answer or reason before saving this decision.")
            option_passages = list(dict.fromkeys(e.passage_id for e in case.report.evidence if option and e.id in option.evidence_ids))
            case.resolutions.append(Resolution(finding_id=data.finding_id, action=data.action, answer=answer, owner=data.owner.strip(), source_fingerprint=fingerprint(case), option_text=option.text if option else "", option_evidence_ids=option.evidence_ids if option else [], option_passage_ids=option_passages, finding_title=finding.title, finding_question=finding.question, source_snapshot=decision_sources(case, finding, option.evidence_ids if option else []), choice_id=choice.id if choice else ''))
            return start(case)

    @app.post("/api/cases/{case_id}/cancel")
    def cancel(case_id: str):
        with gate:
            case = get(case_id)
            if not case.run or case.run.status != "running":
                raise HTTPException(409, "This review is no longer running.")
            case.run.status = "cancelled"
            case.run.stage = "Review cancelled"
            case.run.error = "The result of this run will not be applied. An AI request already sent may still finish and incur usage. Your inputs are saved."
            case.run.finished_at = now()
            return store.save(case)

    @app.post("/api/cases/{case_id}/resolutions/{resolution_id}/undo", status_code=202)
    def undo(case_id: str, resolution_id: str, data: VersionInput):
        with gate:
            case = editable(case_id, data.version)
            resolution = next((r for r in case.resolutions if r.id == resolution_id), None)
            if not resolution:
                raise HTTPException(404, "Resolution not found.")
            # Undo this choice and any newer choice on the same finding to avoid resurrecting a hidden answer.
            for r in case.resolutions:
                if r.finding_id == resolution.finding_id and r.created_at >= resolution.created_at:
                    r.revoked = True
            return start(case)

    @app.get("/api/cases/{case_id}/brief", response_class=PlainTextResponse)
    def export(case_id: str):
        case = get(case_id)
        if not case.report:
            raise HTTPException(400, "Run the review first.")
        if case.run and case.run.status != "completed":
            raise HTTPException(409, "A recheck is pending or failed. Complete a fresh review before exporting its brief.")
        for prior in case.report.prior_decisions:
            current = store.get_decision(prior.id)
            if current is None or current.project_id != case.project_id or digest(current) != digest(prior):
                raise HTTPException(409, 'An earlier project decision used by this report changed or was removed. Recheck before preparing the brief.')
        return brief(case)

    dist = ROOT / "frontend" / "dist"
    if serve_frontend and os.getenv('CONTEXTGUARD_API_ONLY') != '1' and (dist / 'index.html').is_file() and (dist / 'assets').is_dir():
        from fastapi.staticfiles import StaticFiles
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")
        @app.get("/")
        def index():
            return FileResponse(dist / "index.html")
        @app.get("/favicon.svg")
        def favicon():
            return FileResponse(dist / "favicon.svg", media_type="image/svg+xml")
    return app


app = create_app()
