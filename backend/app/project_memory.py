"""Project-scoped recall. SQLite is authoritative; Mem0 OSS is a retrieval index."""
from __future__ import annotations

import hashlib
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, urlparse

import httpx

from .schemas import Case, DecisionSource, PriorDecision


def decision_sources(case, finding, preferred=()):
    if not case.report:
        return []
    passages = {p.id: (s, p) for s in case.sources for p in s.passages}
    refs = {e.id: e for e in case.report.evidence}
    ids = list(dict.fromkeys([*preferred, *finding.evidence_ids]))
    result = []
    for eid in ids:
        if eid not in refs or refs[eid].passage_id not in passages:
            continue
        evidence = refs[eid]
        source, passage = passages[evidence.passage_id]
        result.append(DecisionSource(document_id=source.id, name=source.name, passage_id=passage.id, location=passage.location, quote=evidence.quote))
        if len(result) == 8:
            break
    return result


def decision_records(case: Case) -> list[PriorDecision]:
    from .workflow import active_assertions
    if not case.project_id or case.mode != 'live':
        return []
    findings = {f.id: f for f in case.report.findings} if case.report else {}
    records = []
    for event in active_assertions(case):
        if event.action != 'confirm' or not event.answer.strip():
            continue
        finding = findings.get(event.finding_id)
        title = event.finding_title or (finding.title if finding else '')
        question = event.finding_question or (finding.question if finding else '')
        if not title:
            continue
        sources = event.source_snapshot or (decision_sources(case, finding, event.option_evidence_ids) if finding else [])
        records.append(PriorDecision(id=event.id, project_id=case.project_id, case_id=case.id, case_title=case.title, finding_id=event.finding_id, title=title, question=question, answer=event.answer, owner=event.owner, source_fingerprint=event.source_fingerprint, sources=sources, created_at=event.created_at))
    return records


def digest(record: PriorDecision) -> str:
    return hashlib.sha256(record.model_dump_json().encode()).hexdigest()


class MemoryIndexError(Exception):
    pass


class Mem0Index:
    """The published Mem0 OSS REST contract, without adding another model SDK."""
    def __init__(self, base_url=None, api_key=None, transport=None):
        self.url = (base_url if base_url is not None else os.getenv('MEM0_BASE_URL', '')).rstrip('/')
        self.key = api_key if api_key is not None else os.getenv('MEM0_API_KEY', '')
        self.transport = transport
        if self.url:
            parsed = urlparse(self.url)
            if parsed.username or parsed.password or parsed.query or parsed.fragment or (parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in {'127.0.0.1', 'localhost', '::1'})):
                raise ValueError('Use HTTPS for a remote Mem0 service, or HTTP on localhost.')

    @property
    def configured(self):
        return bool(self.url)

    def request(self, method, path, payload=None):
        try:
            with httpx.Client(timeout=6, transport=self.transport) as client:
                response = client.request(method, self.url + path, json=payload, headers={'X-API-Key': self.key} if self.key else {})
            if method == 'DELETE' and response.status_code == 404:
                return {}
            if response.status_code >= 400:
                raise MemoryIndexError(f'Mem0 returned HTTP {response.status_code}. Local decisions remain available.')
            return response.json()
        except (httpx.HTTPError, ValueError):
            raise MemoryIndexError('Mem0 could not be reached or returned an invalid response. Local decisions remain available.') from None

    def add(self, record):
        content = f'Earlier user clarification; not independently verified.\nQuestion: {record.question}\nAnswer: {record.answer}\nOwner: {record.owner or "Unassigned"}'
        result = self.request('POST', '/memories', {'messages': [{'role': 'user', 'content': content}], 'user_id': 'contextguard:project:' + record.project_id, 'metadata': {'contextguard_decision_id': record.id, 'project_id': record.project_id, 'case_id': record.case_id, 'source_fingerprint': record.source_fingerprint}, 'infer': False})
        rows = result.get('results') if isinstance(result, dict) else None
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict) or not isinstance(rows[0].get('id'), str) or not rows[0]['id']:
            raise MemoryIndexError('Mem0 did not acknowledge the decision. It remains saved locally for retry.')
        return rows[0]['id']

    def delete(self, remote_id):
        self.request('DELETE', '/memories/' + quote(remote_id, safe=''))

    def search(self, project_id, query):
        result = self.request('POST', '/search', {'query': query[:6000], 'filters': {'user_id': 'contextguard:project:' + project_id, 'project_id': project_id}, 'top_k': 16})
        rows = result.get('results') if isinstance(result, dict) else None
        if not isinstance(rows, list):
            raise MemoryIndexError('Mem0 returned an invalid search response. Local decisions remain available.')
        return [r.get('metadata', {}).get('contextguard_decision_id') for r in rows if isinstance(r, dict) and isinstance(r.get('metadata'), dict)]


class ProjectMemory:
    def __init__(self, store, index=None):
        self.store = store
        self.index = index if index is not None else Mem0Index()
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix='project-memory')
        self.sync_lock = threading.Lock()
        self.schedule_lock = threading.Lock()
        self.scheduled = False
        self.dirty = False
        self.closed = False

    def schedule(self):
        if not self.index.configured:
            return
        with self.schedule_lock:
            if self.closed:
                return
            if self.scheduled:
                self.dirty = True
                return
            self.scheduled = True
        def run():
            try:
                while True:
                    self.sync()
                    with self.schedule_lock:
                        if not self.dirty or self.closed:
                            break
                        self.dirty = False
            finally:
                with self.schedule_lock:
                    self.scheduled = False
        self.worker.submit(run)

    def sync(self):
        if not self.index.configured:
            return
        with self.sync_lock:
            # Bounded batch; pending/error operations are durable and can be retried.
            for job in self.store.memory_jobs(limit=40):
                remote_id = job['remote_id']
                try:
                    record = self.store.get_decision(job['decision_id'])
                    if record is not None and digest(record) != job['digest']:
                        continue
                    if remote_id:
                        self.index.delete(remote_id)
                        self.store.memory_remote_id(job['decision_id'], '')
                        remote_id = ''
                    if record is not None and job['action'] == 'upsert':
                        remote_id = self.index.add(record)
                    self.store.finish_memory_job(job, remote_id)
                except MemoryIndexError as exc:
                    self.store.fail_memory_job(job, str(exc))

    def recall(self, case):
        if not case.project_id or case.mode != 'live':
            return {'decisions': [], 'retrieval': 'none', 'notice': 'Choose a project to recall decisions from its earlier reviews.', 'index': self.status()}
        query = case.goal + '\n' + case.scope + '\n' + '\n'.join(p.text for s in case.sources if s.status == 'ready' for p in s.passages)[:10000]
        canonical = {r.id: r for r in self.store.decisions(case.project_id, exclude_case_id=case.id)}
        picked = []
        retrieval = 'local'
        notice = 'Earlier user clarifications are context. Reconfirm them when current documents differ.'
        if self.index.configured:
            try:
                ids = self.index.search(case.project_id, query)
                # Never trust remote text or filters as the authority. Undo, deletion,
                # changed inputs and other projects are checked against current SQLite.
                picked = list(dict.fromkeys(eid for eid in ids if isinstance(eid, str) and eid in canonical))[:8]
                retrieval = 'mem0'
            except MemoryIndexError as exc:
                notice = str(exc)
        local = self.store.search_decisions(case.project_id, case.id, query)
        for record in local:
            if record.id not in picked:
                picked.append(record.id)
            if len(picked) == 8:
                break
        self.schedule()
        # An undo may have happened while remote search was in flight.
        canonical = {r.id: r for r in self.store.decisions(case.project_id, exclude_case_id=case.id)}
        return {'decisions': [canonical[eid].model_dump() for eid in picked if eid in canonical], 'retrieval': retrieval, 'notice': notice, 'index': self.status()}

    def status(self):
        stats = self.store.memory_job_status()
        return {'configured': self.index.configured, **stats}

    def close(self):
        with self.schedule_lock:
            self.closed = True
        self.worker.shutdown(wait=True, cancel_futures=True)
