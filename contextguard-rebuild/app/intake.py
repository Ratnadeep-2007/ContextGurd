"""Conversation-first intake. Permissions/coverage/provenance are enforced in code."""
import re
from collections import defaultdict

from .contracts import ConversationRoutes, IntakeRequest, Passage
from .providers import PayloadTooLarge, ProviderFailure
from .review import Reviews
from .service import Rejected, digest, ident, now, require


class Intake(Reviews):
    def candidate_projects(self, actor, selected=None):
        projects = []
        if selected is not None:
            require(bool(selected), 'Choose at least one project, or use automatic matching.')
            rows = [self.project(actor, pid) for pid in dict.fromkeys(selected)]
        else:
            rows = self.store.all('project', actor['workspace'])
        for row in rows:
            try:
                project = self.project(actor, row['id'])
            except Rejected:
                continue
            projects.append({k: project.get(k, '') for k in ('id', 'name', 'description', 'goal')})
        require(1 <= len(projects) <= 30, 'Create a project first, or select up to 30 projects for this input.')
        return projects

    def create_intake(self, actor, payload):
        payload = IntakeRequest.model_validate(payload)
        require(payload.consent, 'Confirm you are authorized to process this content.', 403)
        require(payload.test_mode or payload.model_consent,
                'Authorize sending the complete input and eligible project descriptions to model providers.', 403)
        candidates = self.candidate_projects(actor, payload.project_ids)
        for source in payload.sources:
            self.source(actor, source.source_id)
            if payload.project_ids is None:
                mapping = self.store.get('mapping', 'mapping-' + source.source_id)
                if mapping:
                    self.project(actor, mapping['project_id'])
        chars = sum(len(p.text) for source in payload.sources for p in source.passages)
        require(chars <= 60000 and any(p.text.strip() or p.deleted for s in payload.sources for p in s.passages),
                'Use up to 60,000 extracted characters per batch. Nothing was truncated.')
        require(all(p.deleted or (p.text.strip() and p.extraction != 'failed')
                    for source in payload.sources for p in source.passages),
                'This input includes unreadable/deleted passages. Check the source or paste readable text.')
        data = payload.model_dump(mode='json')
        fingerprint = digest({'actor': actor['id'], 'request': data, 'projects': candidates})
        with self.store.transaction():
            previous = next((j for j in self.store.all('intake', actor['workspace'])
                             if j['fingerprint'] == fingerprint), None)
            if previous:
                if previous['status'] == 'failed' and previous['input']:
                    stamp = now()
                    previous.update(status='queued', updated=stamp, attempt_started=stamp,
                                    attempt=previous.get('attempt', 1) + 1, error=None, review_ids=[], providers=[],
                                    units_total=0, units_processed=0, analysis_total=0, analysis_done=0)
                    self.store.put('intake', previous)
                    return self.intake(actor, previous['id']), True
                return self.intake(actor, previous['id']), False
            stamp = now()
            job = {'id': ident(), 'workspace': actor['workspace'], 'actor': actor['id'],
                   'created': stamp, 'updated': stamp, 'attempt_started': stamp, 'attempt': 1,
                   'status': 'queued', 'input': data,
                   'source_ids': [s.source_id for s in payload.sources], 'project_ids': [p['id'] for p in candidates],
                   'fingerprint': fingerprint, 'test_mode': payload.test_mode, 'review_ids': [], 'providers': [],
                   'units_total': 0, 'units_processed': 0, 'analysis_total': 0, 'analysis_done': 0,
                   'discarded_units': 0, 'uncertain_units': 0,
                   'retained_passages': 0, 'error': None}
            return self.store.put('intake', job), True

    def intake(self, actor, job_id):
        job = self.entity(actor, 'intake', job_id)
        require(job['actor'] == actor['id'] or actor['role'] == 'owner', 'Processing record is private.', 403)
        for sid in job['source_ids']:
            self.source(actor, sid)
        # The complete pending input never goes into state/poll responses.
        return {k: v for k, v in job.items() if k not in {'input', 'fingerprint'}}

    def retry_intake(self, actor, job_id):
        self.intake(actor, job_id)
        with self.store.transaction():
            job = self.entity(actor, 'intake', job_id)
            require(job['actor'] == actor['id'], 'Only the person who enabled processing can retry it.', 403)
            require(job['status'] == 'failed' and job['input'], 'Only a failed retained input can be retried.')
            self.candidate_projects(actor, job['project_ids'])
            stamp = now()
            job.update(status='queued', updated=stamp, attempt_started=stamp,
                       attempt=job.get('attempt', 1) + 1, error=None, review_ids=[], providers=[],
                       units_total=0, units_processed=0, analysis_total=0, analysis_done=0)
            self.store.put('intake', job)
        return self.intake(actor, job_id)

    def _classify_batch(self, batch, candidates, context):
        """Classify one routing batch, splitting in half after HTTP 413.

        Cross-batch context (neighbouring units, routing history) travels with
        each half unchanged, and merged routes are coverage-checked by the
        caller exactly like a single-batch result.
        """
        try:
            proposal, provider = self.providers.classify(batch, candidates, context)
        except PayloadTooLarge as exc:
            if len(batch) <= 1:
                raise ProviderFailure(
                    'One passage still exceeds the model request limit after automatic '
                    'splitting; select fewer projects or shorten the passage. ' + str(exc)) from None
            middle = len(batch) // 2
            left, left_provider = self._classify_batch(batch[:middle], candidates, context)
            right, _ = self._classify_batch(batch[middle:], candidates, context)
            return ConversationRoutes(routes=left.routes + right.routes), left_provider
        return ConversationRoutes.model_validate(proposal), provider

    @staticmethod
    def units(payload):
        result = []
        for source in payload.sources:
            for index, passage in enumerate(source.passages):
                if passage.deleted:
                    continue
                # Exact offsets cover every non-whitespace character, including punctuation.
                spans = list(re.finditer(r'\S[\s\S]*?(?:(?<=[.!?])(?=\s|$)|(?=\n)|$)', passage.text))
                for span in spans:
                    start, end = span.span()
                    while start < end:
                        stop = min(start + 1800, end)
                        if stop < end:
                            space = passage.text.rfind(' ', start + 900, stop)
                            if space > start:
                                stop = space
                        if passage.text[start:stop].strip():
                            result.append({'id': 'u' + str(len(result)), 'source_id': source.source_id,
                                           'passage_index': index, 'start': start, 'end': stop,
                                           'text': passage.text[start:stop], 'location': passage.location,
                                           'author': passage.author, 'timestamp': passage.model_dump(mode='json')['timestamp']})
                        start = stop
        require(len(result) <= 1000, 'Use a smaller input; the complete text exceeded 1,000 units.')
        # Never silently omit a paragraph, a sentence, or punctuation during preprocessing.
        for source in payload.sources:
            for index, passage in enumerate(source.passages):
                if passage.deleted:
                    continue
                original = re.sub(r'\s', '', passage.text)
                covered = ''.join(re.sub(r'\s', '', u['text']) for u in result
                                  if u['source_id'] == source.source_id and u['passage_index'] == index)
                require(original == covered, 'Input coverage validation failed; nothing was discarded.')
        return result

    @staticmethod
    def fixture_routes(units, candidates, previous=None):
        """Explicit fictional mode only; never a provider-error fallback."""
        current, routes = previous, []
        ignored_words = {'test', 'fictional', 'project', 'pilot', 'the'}
        for unit in units:
            matches = []
            allowed = set(unit.get('allowed_project_ids') or [p['id'] for p in candidates])
            for project in candidates:
                if project['id'] not in allowed:
                    continue
                tokens = set(re.findall(r'[a-z]{3,}', project['name'].casefold())) - ignored_words
                if tokens and any(re.search(r'\b' + re.escape(t) + r'\b', unit['text'].casefold()) for t in tokens):
                    matches.append(project['id'])
            if len(matches) == 1:
                current = matches[0]
            chatter = any(t in unit['text'].casefold() for t in ('weekend', 'lunch', 'weather', 'football'))
            if chatter:
                current = None
            chosen = None if chatter or len(matches) > 1 or current not in allowed else current
            routes.append({'unit_id': unit['id'], 'disposition': 'matched' if chosen else 'irrelevant',
                           'project_id': chosen, 'reason': 'Fictional deterministic routing fixture; no live AI.'})
        return ConversationRoutes(routes=routes), current

    def _progress(self, job_id, **changes):
        with self.store.transaction():
            job = self.store.get('intake', job_id)
            job.update(**changes, updated=now())
            self.store.put('intake', job)
        return job

    def process_intake(self, job_id):
        job = self.store.get('intake', job_id)
        if not job or job['status'] != 'queued':
            return
        try:
            actor = self.store.get('user', job['actor'])
            payload = IntakeRequest.model_validate(job['input'])
            candidates = self.candidate_projects(actor, job['project_ids'])
            for source in payload.sources:
                self.source(actor, source.source_id)
            units = self.units(payload)
            mappings = {}
            if payload.project_ids is None:
                for source in payload.sources:
                    mapped = self.store.get('mapping', 'mapping-' + source.source_id)
                    if mapped:
                        self.project(actor, mapped['project_id'])
                        mappings[source.source_id] = mapped['project_id']
                for unit in units:
                    if unit['source_id'] in mappings:
                        unit['allowed_project_ids'] = [mappings[unit['source_id']]]
            self._progress(job_id, status='routing', units_total=len(units), units_processed=0)
            routes, providers, history, fixture_current = [], [], [], None
            offset = 0
            while offset < len(units):
                batch, size = [], 0
                while offset + len(batch) < len(units) and len(batch) < 25:
                    unit = units[offset + len(batch)]
                    if batch and size + len(unit['text']) > 8000:
                        break
                    batch.append(unit)
                    size += len(unit['text'])
                if payload.test_mode:
                    proposal, fixture_current = self.fixture_routes(batch, candidates, fixture_current)
                    provider = 'Fictional routing fixture — no live AI'
                    proposal = ConversationRoutes.model_validate(proposal)
                else:
                    proposal, provider = self._classify_batch(batch, candidates, {
                        'previous_project_passages': history[-6:],
                        'following_units': units[offset + len(batch):offset + len(batch) + 4]})
                received = [r.unit_id for r in proposal.routes]
                require(len(received) == len(set(received)) and set(received) == {u['id'] for u in batch},
                        'The model did not cover every input unit exactly once. Input retained for retry.')
                eligible = {p['id'] for p in candidates}
                batch_units = {u['id']: u for u in batch}
                for route in proposal.routes:
                    require((route.disposition == 'matched' and route.project_id in eligible) or
                            (route.disposition != 'matched' and route.project_id is None),
                            'The model returned an invalid project route. Input retained for retry.')
                    require(route.disposition != 'matched' or route.project_id in
                            batch_units[route.unit_id].get('allowed_project_ids', eligible),
                            'A project route conflicts with the approved source mapping. Input retained for retry.')
                routes.extend(proposal.routes)
                providers.append(provider)
                lookup = {r.unit_id: r for r in proposal.routes}
                history.extend({'text': u['text'], 'project_id': lookup[u['id']].project_id}
                               for u in batch if lookup[u['id']].disposition == 'matched')
                offset += len(batch)
                self._progress(job_id, units_processed=offset, providers=list(dict.fromkeys(providers)))
            # Validate access again after external calls, before writing routed evidence or reading memory.
            require(self.candidate_projects(actor, job['project_ids']) == candidates,
                    'Project descriptions or goals changed during matching. Retry the retained input.')
            for source in payload.sources:
                self.source(actor, source.source_id)
                if payload.project_ids is None:
                    current_mapping = self.store.get('mapping', 'mapping-' + source.source_id)
                    require((current_mapping or {}).get('project_id') == mappings.get(source.source_id),
                            'A source mapping changed during matching. Retry the retained input.')
            by_id = {r.unit_id: r for r in routes}
            groups = defaultdict(list)
            for unit in units:
                route = by_id[unit['id']]
                if route.disposition == 'matched':
                    groups[(route.project_id, unit['source_id'], unit['passage_index'])].append(unit)
            project_sources = defaultdict(set)
            retained, current_ids = 0, set()
            with self.store.transaction():
                for (pid, sid, index), parts in groups.items():
                    project = self.project(actor, pid)
                    source = self.source(actor, sid)
                    original = next(s for s in payload.sources if s.source_id == sid).passages[index]
                    grants = list(project['members']) if payload.share else []
                    routed = self.create_source(actor, source['type'], ('routed:' + sid + ':' + pid),
                                                (source['label'] + ' · ' + project['name'])[:150], grants)
                    if payload.share:
                        self.source_grants(actor, routed['id'], list(set(routed['allowed_users']) | set(grants)))
                    passages = []
                    # Sentence-level evidence lets opposing claims in one transcript retain distinct citations.
                    for part in parts:
                        text = original.text[part['start']:part['end']]
                        passages.append(Passage(**{**original.model_dump(mode='json'),
                            'item_id': digest({'origin': original.item_id, 'start': part['start']})[:40], 'text': text,
                            'details': {**original.details, 'origin_source_id': sid, 'origin_item_id': original.item_id,
                                        'start_char': part['start'], 'end_char': part['end'], 'intake_id': job_id,
                                        'routing_reason': by_id[part['id']].reason}}))
                    for start in range(0, len(passages), 300):
                        batch = passages[start:start + 300]
                        saved = self.ingest(actor, {'source_id': routed['id'], 'project_id': pid, 'consent': True,
                            'test_mode': payload.test_mode, 'passages': [p.model_dump(mode='json') for p in batch],
                            'original': {'origin_source_id': sid, 'project_id': pid, 'retained_passages':
                                         [p.model_dump(mode='json') for p in batch], 'unrelated_content_removed': True}})
                        current_ids.update(e['id'] for e in saved)
                    retained += len(passages)
                    project_sources[pid].add(routed['id'])
                observed = {(s.source_id, p.item_id) for s in payload.sources for p in s.passages}
                eligible = {p['id'] for p in candidates}
                for old in self.store.all('evidence', actor['workspace']):
                    origin = (old['details'].get('origin_source_id'), old['details'].get('origin_item_id'))
                    if old['active'] and old['id'] not in current_ids and origin in observed and old['project_id'] in eligible:
                        self.project(actor, old['project_id'])
                        self.source(actor, old['source_id'])
                        old.update(active=False, availability='superseded_by_processed_source_revision')
                        self.store.put('evidence', old)
            self._progress(job_id, status='analyzing', retained_passages=retained, analysis_done=0, analysis_total=0)
            review_ids = []
            for pid in project_sources:
                project = self.project(actor, pid)
                source_ids = sorted({e['source_id'] for e in self.visible_evidence(actor, pid) if not e['deleted']})
                goal = payload.goal.strip() or project.get('goal') or ('Check whether ' + project['name'] + ' has enough reliable context to proceed.')
                review = self.analyze(actor, pid, goal, source_ids, consent=payload.model_consent, test_mode=payload.test_mode,
                                      intake_id=job_id, on_progress=lambda done, total: self._progress(
                                          job_id, analysis_done=done, analysis_total=total))
                review['intake_id'] = job_id
                review['limitations'].append(f'Input matching checked all {len(units)} units; '
                    f'{sum(r.disposition != "matched" for r in routes)} unmatched units were omitted. '
                    'This report covers only the retained project passages; matching is model interpretation, not proof of relevance.')
                self.store.put('review', review)
                review_ids.append(review['id'])
                self._progress(job_id, review_ids=review_ids)
                require(review['status'] == 'complete' and not any(x.startswith('Rejected finding:') for x in review['failures']),
                        'Project analysis failed citation/provider checks. Complete input retained for retry.')
            # Only successful, coverage-verified processing removes raw/unmatched content.
            require(self.candidate_projects(actor, job['project_ids']) == candidates,
                    'Project descriptions or goals changed during analysis. Retry the retained input.')
            for source in payload.sources:
                self.source(actor, source.source_id)
            for review_id in review_ids:
                require(not self.get_review(actor, review_id)['stale'],
                        'Source evidence changed during analysis. Retry the retained input.')
            self._progress(job_id, status='complete', input={}, error=None,
                           discarded_units=sum(r.disposition != 'matched' for r in routes),
                           uncertain_units=sum(r.disposition == 'uncertain' for r in routes), review_ids=review_ids)
        except (ProviderFailure, Rejected) as exc:
            message = exc.message if isinstance(exc, Rejected) else str(exc)
            self._progress(job_id, status='failed', error=message)
        except Exception:
            self._progress(job_id, status='failed', error='Processing could not finish. The complete input is retained for retry.')
