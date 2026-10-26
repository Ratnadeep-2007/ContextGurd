import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timezone
from uuid import uuid4

from .contracts import Delivery
from .storage import atomic


def now():
    return datetime.now(timezone.utc).isoformat()


def ident():
    return uuid4().hex


class Rejected(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status


def require(condition, message, status=400):
    if not condition:
        raise Rejected(message, status)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class Service:
    def __init__(self, store):
        self.store = store

    @atomic
    def create_user(self, username, password, actor=None):
        require(2 <= len(username.strip()) <= 60 and 10 <= len(password) <= 200,
                'Use a name and a password of at least 10 characters.')
        users = self.store.all('user')
        if users:
            require(actor and actor['role'] == 'owner', 'Only a workspace owner can add accounts.', 403)
        require(not any(u['username'].casefold() == username.strip().casefold() for u in users), 'Name already exists.')
        salt = secrets.token_hex(16)
        row = {'id': ident(), 'workspace': actor['workspace'] if actor else ident(), 'username': username.strip(),
               'role': 'member' if users else 'owner', 'salt': salt,
               'password': hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 310000).hex()}
        self.store.put('user', row)
        return self.public_user(row)

    @staticmethod
    def public_user(user):
        return {k: user[k] for k in ('id', 'workspace', 'username', 'role')} | {
            'display_name': user.get('display_name', user['username']),
            'is_demo': bool(user.get('test_fixture')), 'responsibility': user.get('responsibility_label', '')}

    @atomic
    def login(self, username, password):
        user = next((u for u in self.store.all('user') if u['username'].casefold() == username.casefold()), None)
        salt = bytes.fromhex(user['salt']) if user else b'0' * 16
        value = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 310000).hex()
        require(user and hmac.compare_digest(user['password'], value), 'Invalid name or password.', 401)
        token = secrets.token_urlsafe(32)
        self.store.put('session', {'id': hashlib.sha256(token.encode()).hexdigest(), 'workspace': user['workspace'],
                                   'user_id': user['id'], 'expires': time.time() + 8 * 3600})
        return token

    def actor(self, token):
        session = self.store.get('session', hashlib.sha256((token or '').encode()).hexdigest())
        require(session and session['expires'] > time.time(), 'Sign in to continue.', 401)
        return self.store.get('user', session['user_id'])

    def entity(self, actor, kind, key):
        row = self.store.get(kind, key)
        require(row and row['workspace'] == actor['workspace'], 'Item not found.', 404)
        return row

    def project(self, actor, key, roles=None):
        row = self.entity(actor, 'project', key)
        role = 'owner' if actor['role'] == 'owner' else row['members'].get(actor['id'])
        require(role and (not roles or role in roles), 'Project permission denied.', 403)
        return row

    def source(self, actor, key):
        row = self.entity(actor, 'source', key)
        require(actor['role'] == 'owner' or actor['id'] in row['allowed_users'], 'Source permission denied.', 403)
        return row

    @atomic
    def create_project(self, actor, name, description='', goal=''):
        require(2 <= len(name.strip()) <= 120, 'Provide a project name.')
        require(isinstance(description, str) and len(description) <= 2000 and isinstance(goal, str) and len(goal) <= 1500,
                'Use a project description under 2,000 characters and goal under 1,500 characters.')
        return self.store.put('project', {'id': ident(), 'workspace': actor['workspace'], 'name': name.strip(),
                                         'description': description.strip(), 'goal': goal.strip(),
                                         'members': {actor['id']: 'owner'}, 'responsibilities': {}})

    @atomic
    def update_project(self, actor, project_id, description, goal):
        project = self.project(actor, project_id, {'owner'})
        require(isinstance(description, str) and len(description) <= 2000 and isinstance(goal, str) and len(goal) <= 1500,
                'Use a project description under 2,000 characters and goal under 1,500 characters.')
        project.update(description=description.strip(), goal=goal.strip())
        return self.store.put('project', project)

    @atomic
    def member(self, actor, project_id, user_id, role):
        project = self.project(actor, project_id, {'owner'})
        self.entity(actor, 'user', user_id)
        require(role in {'owner', 'decision_owner', 'reviewer'}, 'Unknown role.')
        project['members'][user_id] = role
        return self.store.put('project', project)

    @atomic
    def responsibility(self, actor, project_id, topic, user_id):
        project = self.project(actor, project_id, {'owner'})
        require(user_id in project['members'], 'Select a project member.')
        require(2 <= len(topic.strip()) <= 100, 'Supply a responsibility topic.')
        project['responsibilities'][topic.casefold().strip()] = user_id
        return self.store.put('project', project)

    @atomic
    def create_source(self, actor, source_type, container, label, allowed_users=None):
        require(source_type in {'manual', 'vexa', 'slack', 'whatsapp'}, 'Unknown source type.')
        require(container and len(container) <= 300 and 1 <= len(label) <= 150, 'Name the selected source.')
        existing = next((s for s in self.store.all('source', actor['workspace'])
                         if s['type'] == source_type and s['container'] == container), None)
        if existing:
            return self.source(actor, existing['id'])
        allowed = list(set((allowed_users or []) + [actor['id']]))
        for uid in allowed:
            self.entity(actor, 'user', uid)
        return self.store.put('source', {'id': ident(), 'workspace': actor['workspace'], 'type': source_type,
                                        'container': container, 'label': label, 'allowed_users': allowed,
                                        'created_by': actor['id'], 'created': now()})

    @atomic
    def map_source(self, actor, source_id, project_id):
        source = self.source(actor, source_id)
        require(actor['role'] == 'owner' or actor['id'] == source['created_by'], 'Only the source owner can map it.', 403)
        self.project(actor, project_id, {'owner'})
        return self.store.put('mapping', {'id': 'mapping-' + source_id, 'workspace': actor['workspace'],
                                         'source_id': source_id, 'project_id': project_id, 'approved_by': actor['id'], 'date': now()})

    @atomic
    def source_grants(self, actor, source_id, allowed_users):
        source = self.source(actor, source_id)
        require(actor['role'] == 'owner' or source['created_by'] == actor['id'], 'Only the source owner can change access.', 403)
        for uid in allowed_users:
            self.entity(actor, 'user', uid)
        source['allowed_users'] = list(set(allowed_users + [source['created_by']]))
        source['access_actor'], source['access_date'] = actor['id'], now()
        return self.store.put('source', source)

    @atomic
    def ingest(self, actor, delivery):
        delivery = Delivery.model_validate(delivery)
        require(delivery.consent, 'Confirm you are authorized to process this selected source.', 403)
        source = self.source(actor, delivery.source_id)
        project_id = delivery.project_id
        mapping = self.store.get('mapping', 'mapping-' + source['id'])
        if project_id:
            self.project(actor, project_id)
        elif mapping:
            self.project(actor, mapping['project_id'])
            project_id = mapping['project_id']
        # Validate all routes before saving or comparing anything to project memory.
        event = {'id': ident(), 'workspace': actor['workspace'], 'source_id': source['id'], 'actor': actor['id'],
                 'consent_date': now(), 'original': delivery.original, 'test_mode': delivery.test_mode}
        existing = self.store.all('evidence', actor['workspace'])
        result = []
        for passage in delivery.passages:
            payload = passage.model_dump(mode='json')
            fingerprint = digest({'passage': payload, 'test_mode': delivery.test_mode})
            previous = next((e for e in reversed(existing) if e['source_id'] == source['id'] and e['item_id'] == passage.item_id and e['active']), None)
            if previous and previous['project_id']:
                # Source access alone never permits reading or revising another project's routed item.
                self.project(actor, previous['project_id'])
            if previous and previous['fingerprint'] == fingerprint:
                require(not project_id or previous['project_id'] == project_id,
                        'This item already has a route. Use a confirmed segment for another project.')
                result.append(previous)
                continue
            if previous:
                require(not project_id or not previous['project_id'] or previous['project_id'] == project_id,
                        'Do not silently move a revised item between projects.')
                previous['active'] = False
                self.store.put('evidence', previous)
            row = {'id': ident(), 'workspace': actor['workspace'], 'source_id': source['id'], 'source_type': source['type'],
                   'container': source['container'], **payload, 'event_id': event['id'], 'active': True,
                   'project_id': previous['project_id'] if previous and previous['project_id'] else project_id,
                   'routing': 'confirmed' if project_id or (previous and previous['project_id']) else 'unknown',
                   'route_actor': actor['id'] if project_id else None, 'test_mode': delivery.test_mode,
                   'fingerprint': fingerprint, 'previous_id': previous['id'] if previous else None,
                   'received': now(), 'consent_actor': actor['id']}
            self.store.put('evidence', row)
            existing.append(row)
            result.append(row)
        self.store.put('source_event', event)
        return result

    def visible_evidence(self, actor, project_id=None, unknown=False):
        if project_id:
            self.project(actor, project_id)
        rows = []
        for e in self.store.all('evidence', actor['workspace']):
            if not e['active'] or (project_id and e['project_id'] != project_id) or (unknown and e['routing'] != 'unknown'):
                continue
            try:
                self.source(actor, e['source_id'])
                if e['project_id']:
                    self.project(actor, e['project_id'])
                rows.append(e)
            except Rejected:
                continue
        return rows

    @atomic
    def route(self, actor, evidence_id, project_id=None, action='assign'):
        evidence = self.entity(actor, 'evidence', evidence_id)
        self.source(actor, evidence['source_id'])
        require(evidence['active'] and evidence['routing'] == 'unknown', 'Only active unknown evidence can be routed.')
        require(action in {'assign', 'keep', 'dismiss'}, 'Unknown routing action.')
        if action == 'assign':
            self.project(actor, project_id)
            evidence.update(project_id=project_id, routing='confirmed', route_actor=actor['id'], route_date=now())
        elif action == 'dismiss':
            evidence.update(routing='dismissed', route_actor=actor['id'], route_date=now())
        return self.store.put('evidence', evidence)

    @atomic
    def segment(self, actor, evidence_id, project_id, quote):
        parent = self.entity(actor, 'evidence', evidence_id)
        self.source(actor, parent['source_id'])
        self.project(actor, project_id)
        require(not parent.get('parent_id'), 'Select a passage from the complete original, not a nested segment.')
        require(parent['active'] and not parent['deleted'] and len(quote.strip()) >= 4 and quote in parent['text'],
                'A confirmed segment must be an exact passage from an active source.')
        row = {**parent, 'id': ident(), 'item_id': parent['item_id'] + ':segment:' + ident(),
               'parent_id': parent['id'], 'text': quote, 'project_id': project_id, 'routing': 'confirmed',
               'route_actor': actor['id'], 'route_date': now()}
        row['fingerprint'] = digest({'parent': parent['fingerprint'], 'quote': quote})
        return self.store.put('evidence', row)

    def suggestions(self, actor, evidence_id):
        evidence = self.entity(actor, 'evidence', evidence_id)
        self.source(actor, evidence['source_id'])
        require(evidence['routing'] == 'unknown', 'Suggestions are only for unknown context.')
        # Conservative local hints, explicitly not model certainty or a confirmed route.
        suggestions = []
        for project in self.store.all('project', actor['workspace']):
            try:
                self.project(actor, project['id'])
            except Rejected:
                continue
            if project['name'].casefold() in evidence['text'].casefold():
                suggestions.append({'project_id': project['id'], 'name': project['name'],
                                    'reason': 'Project name appears in the passage; human confirmation required.', 'confirmed': False})
        return suggestions
