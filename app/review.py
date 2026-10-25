from .contracts import Analysis, Citation, ProposedFinding
from .providers import ProviderFailure, Providers
from .service import Service, digest, ident, now, require
from .storage import atomic


class Reviews(Service):
    def __init__(self, store, providers=None):
        super().__init__(store)
        self.providers = providers or Providers()

    def decisions(self, actor, project_id):
        self.project(actor, project_id)
        visible = []
        for d in self.store.all('decision', actor['workspace']):
            if d['project_id'] != project_id:
                continue
            try:
                for cite in d['citations']:
                    self.source(actor, self.entity(actor, 'evidence', cite['evidence_id'])['source_id'])
                visible.append(d)
            except Exception as exc:
                from .service import Rejected
                if not isinstance(exc, Rejected):
                    raise
        for decision in visible:
            decision['superseded_by'] = [d['id'] for d in visible if d.get('supersedes') == decision['id']]
            decision['support_current'] = all(self.current(self.entity(actor, 'evidence', c['evidence_id'])) for c in decision['citations'])
        return visible

    def model_suggestions(self, actor, evidence_id, consent):
        evidence = self.entity(actor, 'evidence', evidence_id)
        self.source(actor, evidence['source_id'])
        require(evidence['active'] and evidence['routing'] == 'unknown', 'Only active unknown context needs a routing suggestion.')
        require(consent is True, 'Confirm this passage and accessible project names may be sent to the model.', 403)
        candidates = []
        for project in self.store.all('project', actor['workspace']):
            try:
                self.project(actor, project['id'])
                candidates.append({'id': project['id'], 'name': project['name']})
            except Exception as exc:
                from .service import Rejected
                if not isinstance(exc, Rejected):
                    raise
        require(candidates, 'Create or join a project before requesting suggestions.')
        try:
            proposal, provider = self.providers.suggest(evidence['text'], candidates)
        except ProviderFailure as exc:
            from .service import Rejected
            raise Rejected(str(exc), 409) from None
        allowed = {p['id'] for p in candidates}
        require(all(s.project_id in allowed for s in proposal.suggestions), 'Model returned an inaccessible project; suggestions rejected.')
        return {'provider': provider, 'suggestions': [{**s.model_dump(), 'confirmed': False} for s in proposal.suggestions]}

    def get_review(self, actor, review_id):
        review = self.entity(actor, 'review', review_id)
        self.project(actor, review['project_id'])
        for sid in review['source_ids']:
            self.source(actor, sid)
        for decision in review['memory']:
            for citation in decision['citations']:
                self.source(actor, self.entity(actor, 'evidence', citation['evidence_id'])['source_id'])
        review['stale'] = any(not self.current(e) for e in review['evidence'])
        review['readiness'] = self.readiness(review)
        return review

    def current(self, evidence):
        actual = self.store.get('evidence', evidence['id'])
        if not actual or actual['fingerprint'] != evidence['fingerprint']:
            return False
        visited = set()
        while actual:
            if actual['id'] in visited or len(visited) > 100 or not actual['active'] or actual['deleted']:
                return False
            visited.add(actual['id'])
            if not actual.get('parent_id'):
                return True
            actual = self.store.get('evidence', actual['parent_id'])
        return False

    @staticmethod
    def readiness(review):
        if review.get('stale') or review['status'] != 'complete' or review['failures'] or not review['evidence']:
            return 'Needs clarification'
        open_findings = [f for f in review['findings'] if f['state'] == 'open' and f['kind'] != 'verified_fact']
        if any(f['priority'] == 'high' for f in open_findings):
            return 'Needs clarification'
        return 'Ready with actions' if open_findings else 'Ready'

    @staticmethod
    def verified(proposed, evidence, decisions):
        proposed = ProposedFinding.model_validate(proposed)
        by_id = {e['id']: e for e in evidence}
        require(all(c.evidence_id in by_id and c.quote in by_id[c.evidence_id]['text'] for c in proposed.citations),
                'Model citation does not point to an exact selected passage.')
        require(all(d in {x['id'] for x in decisions} for d in proposed.decision_ids), 'Invalid decision reference.')
        if proposed.kind == 'potential_conflict':
            require(len({c.evidence_id for c in proposed.citations}) >= 2 or proposed.decision_ids,
                    'Potential conflict requires both source sides or a cited prior decision.')
            compared = [by_id[c.evidence_id] for c in proposed.citations]
            boundaries_differ = any(len({e['details'][key] for e in compared if e['details'].get(key)}) > 1
                                    for key in ('scope', 'version', 'period', 'milestone'))
            if boundaries_differ or not (proposed.same_scope and proposed.same_version and proposed.same_period):
                proposed.kind = 'clarification_needed'
                proposed.uncertainty += ' Comparison boundaries differ or remain uncertain; contradiction is not established.'
        return proposed.model_dump(mode='json')

    @atomic
    def analyze(self, actor, project_id, goal, source_ids, start=None, end=None, consent=False, test_mode=False):
        project = self.project(actor, project_id)
        require(type(consent) is bool and type(test_mode) is bool, 'Consent and test mode must be explicit booleans.')
        require(5 <= len(goal.strip()) <= 1500 and 1 <= len(source_ids) <= 20, 'State a goal and select 1–20 sources.')
        require(not start or not end or start <= end, 'The start date must precede the end date.')
        for sid in source_ids:
            self.source(actor, sid)
        rows = [e for e in self.visible_evidence(actor, project_id) if e['source_id'] in source_ids and e['routing'] == 'confirmed' and not e['deleted']]
        failures = []
        for sid in source_ids:
            source = self.source(actor, sid)
            if source.get('last_error'):
                failures.append(source['label'] + ': ' + source['last_error'])
        selected = []
        for e in rows:
            if not self.current(e):
                failures.append(e['location'] + ': original source changed; segment needs reconfirmation')
                continue
            date = (e['timestamp'] or '')[:10]
            if date and ((start and date < start) or (end and date > end)):
                continue
            if (start or end) and not date:
                failures.append('Date unknown: ' + e['location'])
            if e['extraction'] != 'complete':
                failures.append(e['location'] + ': ' + e['extraction'])
            if e['text'].strip():
                selected.append(e)
        require(len(selected) <= 300, 'Choose fewer sources; this review exceeds 300 passages.')
        for sid in source_ids:
            if not any(e['source_id'] == sid for e in selected):
                failures.append(self.source(actor, sid)['label'] + ': no usable routed passages in the selected date range')
        review = {'id': ident(), 'workspace': actor['workspace'], 'project_id': project_id, 'owner_id': actor['id'],
                  'goal': goal.strip(), 'source_ids': list(dict.fromkeys(source_ids)), 'start': start, 'end': end,
                  'evidence': selected, 'memory': self.decisions(actor, project_id) if selected else [], 'findings': [], 'failures': failures,
                  'limitations': ['Citation verification establishes provenance, not factual truth or exhaustive detection.'],
                  'status': 'complete', 'created': now(), 'test_mode': test_mode, 'provider': None, 'stale': False}
        if not selected:
            review['status'] = 'failed'
            review['limitations'].append('No usable selected project evidence; no analysis generated.')
        else:
            try:
                if test_mode:
                    require(all(e['test_mode'] for e in selected), 'Test analysis only accepts explicitly fictional/test evidence.')
                    analysis = self.fixture(selected)
                    review['provider'] = 'Fictional deterministic test fixture — no live AI'
                else:
                    require(consent, 'Confirm selected passages and prior project decisions may leave this machine.')
                    analysis, review['provider'] = self.providers.analyze(goal, selected, review['memory'])
                for proposed in analysis.findings:
                    try:
                        finding = self.verified(proposed, selected, review['memory'])
                    except Exception as exc:
                        from .service import Rejected
                        if not isinstance(exc, Rejected):
                            raise
                        review['failures'].append('Rejected finding: invalid source/decision citation or unsupported comparison.')
                        continue
                    suggested = next((uid for topic, uid in project['responsibilities'].items() if topic in (finding['title'] + ' ' + finding['impact']).casefold()), None)
                    finding.update(id=ident(), state='open', assignee_id=None, suggested_assignee_id=suggested,
                                   collaborators=[], watchers=[], responses=[], confirmed=None, dismissal=None)
                    review['findings'].append(finding)
                review['limitations'] += analysis.limitations
            except ProviderFailure as exc:
                review['status'] = 'failed'
                review['failures'].append(str(exc))
        review['readiness'] = self.readiness(review)
        return self.store.put('review', review)

    @staticmethod
    def fixture(evidence):
        # Fixed fictional cases, never used as a fallback after a model failure.
        proposals = []
        pairs = [('pilot release is January 18', 'pilot release is January 25', 'potential_conflict', 'Pilot date disagreement', 'high'),
                 ('security approval is pending', None, 'missing_information', 'Security approval is missing', 'high'),
                 ('assume the service is free', None, 'unsupported_assumption', 'Service cost assumption', 'medium'),
                 ('depends on vendor credentials', None, 'unresolved_dependency', 'Vendor credentials dependency', 'high'),
                 ('old v1 decision', None, 'possibly_outdated', 'Earlier version needs review', 'low'),
                 ('must be fast', None, 'clarification_needed', 'Performance target is unclear', 'medium')]
        for first, second, kind, title, priority in pairs:
            found = [e for e in evidence if first in e['text']]
            other = [e for e in evidence if second and second in e['text']]
            if found and (not second or other):
                proposals.append(ProposedFinding(kind=kind, title=title, impact='This affects whether the fictional pilot can proceed.',
                    question='What should the team follow for this pilot?', next_action='Ask the accountable decision owner to clarify.',
                    priority=priority, citations=[{'evidence_id': found[0]['id'], 'quote': found[0]['text']}] +
                        ([{'evidence_id': other[0]['id'], 'quote': other[0]['text']}] if second else []),
                    uncertainty='Fictional fixture for workflow testing; not a live inference or truth assessment.',
                    same_scope=True, same_version=True, same_period=True))
        return Analysis(findings=proposals, limitations=['Fictional deterministic fixture; supports only the documented sample phrases.'])

    def finding(self, actor, review_id, finding_id):
        review = self.get_review(actor, review_id)
        require(not review['stale'] and review['status'] == 'complete', 'Evidence changed or analysis failed. Run a new review.', 409)
        finding = next((f for f in review['findings'] if f['id'] == finding_id), None)
        require(finding, 'Finding not found.', 404)
        return review, finding

    @atomic
    def assign(self, actor, review_id, finding_id, assignee_id=None, collaborators=None, watchers=None):
        review, finding = self.finding(actor, review_id, finding_id)
        require(actor['id'] == review['owner_id'], 'Only the review owner can confirm assignment.', 403)
        require(finding['state'] == 'open', 'Closed findings retain their recorded assignment.')
        project = self.project(actor, review['project_id'])
        for uid in ([assignee_id] if assignee_id else []) + (collaborators or []) + (watchers or []):
            require(uid in project['members'], 'Select a project member.')
            member = self.entity(actor, 'user', uid)
            for sid in review['source_ids']:
                self.source(member, sid)
        finding.update(assignee_id=assignee_id, collaborators=collaborators or [], watchers=watchers or [],
                       assignment_actor=actor['id'], assignment_date=now())
        return self.store.put('review', review)

    @atomic
    def respond(self, actor, review_id, finding_id, answer, citations=None, answer_known=True):
        review, finding = self.finding(actor, review_id, finding_id)
        require(finding['state'] == 'open', 'This finding is already closed.')
        require(actor['id'] in {finding['assignee_id'], review['owner_id']}, 'The accountable assignee or review owner must respond.', 403)
        require(3 <= len(answer.strip()) <= 3000, 'Provide an answer or explain what is still unknown.')
        require(type(answer_known) is bool, 'Choose explicitly whether the answer is known.')
        try:
            citations = [Citation.model_validate(c).model_dump() for c in citations or []]
        except ValueError:
            from .service import Rejected
            raise Rejected('Response citations must contain an exact nonempty passage.') from None
        for citation in citations:
            require(any(e['id'] == citation['evidence_id'] and citation['quote'] in e['text'] for e in review['evidence']), 'Invalid response citation.')
        finding['responses'].append({'id': ident(), 'actor': actor['id'], 'date': now(), 'answer': answer.strip(),
                                     'citations': citations or [], 'answer_known': answer_known})
        # A response does not imply confirmation or resolution.
        return self.store.put('review', review)

    @atomic
    def confirm(self, actor, review_id, finding_id, supersedes=None):
        review, finding = self.finding(actor, review_id, finding_id)
        self.project(actor, review['project_id'], {'owner', 'decision_owner'})
        require(finding['state'] == 'open' and finding['responses'], 'A recorded response is required before confirmation.')
        if supersedes:
            previous = self.entity(actor, 'decision', supersedes)
            require(previous['project_id'] == review['project_id'], 'Decision belongs to another project.')
            require(not any(d.get('supersedes') == supersedes for d in self.store.all('decision', actor['workspace'])), 'This decision has already been superseded.')
        response = finding['responses'][-1]
        require(response['answer_known'] is True, 'An unknown answer stays unresolved. Record the impact and next action instead.')
        decision = {'id': ident(), 'workspace': actor['workspace'], 'project_id': review['project_id'],
                    'text': response['answer'], 'confirmed_by': actor['id'], 'confirmed_at': now(),
                    'response_actor': response['actor'], 'citations': response['citations'] or finding['citations'],
                    'supersedes': supersedes, 'review_id': review_id, 'finding_id': finding_id}
        decision['citation_role'] = 'response_support' if response['citations'] else 'finding_context_only'
        self.store.put('decision', decision)
        finding.update(state='resolved', confirmed=decision['id'])
        self.store.put('review', review)
        return decision

    @atomic
    def dismiss(self, actor, review_id, finding_id, reason):
        review, finding = self.finding(actor, review_id, finding_id)
        require(actor['id'] == review['owner_id'], 'Only the review owner can dismiss a false positive.', 403)
        require(finding['state'] == 'open' and len(reason.strip()) >= 5, 'Explain why this is a false positive.')
        finding.update(state='dismissed', dismissal={'actor': actor['id'], 'date': now(), 'reason': reason.strip()})
        return self.store.put('review', review)

    def brief(self, actor, review_id):
        review = self.get_review(actor, review_id)
        require(not review['stale'], 'Sources changed. Run a new review before exporting.', 409)
        lines = ['# Context Gap Report', '', 'Goal: ' + review['goal'], 'Status: ' + review['readiness'],
                 'Created: ' + review['created'], 'Mode: ' + (review['provider'] or 'Analysis failed'),
                 'Date range: ' + str(review['start'] or 'all') + ' through ' + str(review['end'] or 'all'), '', '## Analyzed sources']
        for e in review['evidence']:
            lines += [f"- {e['source_type']} / {e['location']} / {e['id']} / {e['extraction']}",
                      f"  Author: {e['author'] or 'Unknown'}; timestamp: {e['timestamp'] or 'Unknown'}; link: {e['link'] or 'local source'}"]
        for f in review['findings']:
            lines += ['', '## ' + f['title'], f"{f['kind']} / {f['priority']} / {f['state']}", f['impact'],
                      'Question: ' + f['question'], 'Next action: ' + f['next_action'],
                      'Uncertainty: ' + f['uncertainty'], 'Assignee: ' + str(f['assignee_id'] or 'Unassigned')]
            for c in f['citations']:
                lines += [f"> {c['quote']}", 'Evidence: ' + c['evidence_id']]
            for response in f['responses']:
                lines += [f"Response ({response['actor']}, {response['date']}): {response['answer']}"]
            if f['dismissal']:
                lines += ['Dismissal: ' + str(f['dismissal'])]
            if f['confirmed']:
                lines += ['Confirmed decision: ' + f['confirmed']]
            if f['decision_ids']:
                lines += ['Prior decisions in question: ' + ', '.join(f['decision_ids'])]
        lines += ['', '## Confirmed decision history']
        for d in self.decisions(actor, review['project_id']):
            lines += [f"- {d['id']}: {d['text']} (confirmed by {d['confirmed_by']} at {d['confirmed_at']}; supersedes {d['supersedes'] or 'none'})"]
            lines += ['  Citation role: ' + d.get('citation_role', 'finding_context_only') + '; the human confirmation is distinct from documentary proof.']
        lines += ['', '## Failures and limitations'] + ['- ' + x for x in review['failures'] + review['limitations']]
        return '\n'.join(lines)
