import hashlib
import json
import os
import secrets
import time
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field

from .adapters import AdapterFailure, Slack, Vexa, baileys_events, manual
from .contracts import Contract, Passage
from .credentials import transform
from .review import Reviews
from .service import Rejected, ident, now, require
from .storage import Store

ROOT = Path(__file__).resolve().parents[1]


class Login(Contract):
    username: str = Field(min_length=2, max_length=60)
    password: str = Field(min_length=10, max_length=200)


class Command(Contract):
    action: str = Field(max_length=40)
    payload: dict = Field(default_factory=dict)


def create_app(db_path=None, providers=None, load_settings=True):
    if load_settings:
        load_dotenv(ROOT / '.env', override=False)
    store = Store(db_path or os.getenv('CONTEXTGUARD_DB', str(ROOT / 'data/contextguard.sqlite3')))
    service = Reviews(store, providers)
    attempts = {}

    @asynccontextmanager
    async def lifespan(app):
        yield
        store.db.close()

    app = FastAPI(title='ContextGuard', lifespan=lifespan)
    app.state.service = service

    @app.middleware('http')
    async def boundary(request, call_next):
        host = request.headers.get('host', '').split(':')[0]
        if host not in {'127.0.0.1', 'localhost', 'testserver'}:
            return JSONResponse({'detail': 'This app accepts local hostnames only.'}, 403)
        if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
            origin = request.headers.get('origin')
            if origin and urlsplit(origin).netloc != request.headers.get('host'):
                return JSONResponse({'detail': 'Cross-origin changes are not allowed.'}, 403)
        try:
            if int(request.headers.get('content-length', '0')) > 6 * 1024 * 1024:
                return JSONResponse({'detail': 'Request exceeds 6 MB. Select a smaller excerpt.'}, 413)
        except ValueError:
            return JSONResponse({'detail': 'Invalid request length.'}, 400)
        response = await call_next(request)
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(Rejected)
    async def rejected(request, exc):
        return JSONResponse({'detail': exc.message}, exc.status)

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        # Pydantic's default errors may echo passwords or entire source passages.
        return JSONResponse({'detail': 'Invalid input. Check required fields and limits.'}, 422)

    def actor(request: Request):
        return service.actor(request.cookies.get('cg_session'))

    def owner(user):
        require(user['role'] == 'owner', 'A workspace owner must configure connections.', 403)

    @app.get('/api/health')
    def health():
        return {'product': 'ContextGuard', 'version': 'rebuild',
                'instance_id': hashlib.sha256(str(ROOT.resolve()).casefold().encode()).hexdigest()[:12],
                'setup_required': not bool(store.all('user'))}

    @app.post('/api/setup')
    def setup(payload: Login):
        require(not store.all('user'), 'Setup is already complete.', 409)
        return service.create_user(payload.username, payload.password)

    @app.post('/api/login')
    def login(payload: Login, request: Request):
        key = request.client.host if request.client else 'local'
        stamp, count = attempts.get(key, (time.time(), 0))
        if time.time() - stamp > 60:
            stamp, count = time.time(), 0
        require(count < 10, 'Too many attempts. Try again in one minute.', 429)
        attempts[key] = (stamp, count + 1)
        token = service.login(payload.username, payload.password)
        attempts.pop(key, None)
        response = JSONResponse({'ok': True})
        response.set_cookie('cg_session', token, httponly=True, samesite='strict', max_age=8 * 3600)
        return response

    @app.post('/api/logout')
    def logout(request: Request, user=Depends(actor)):
        session = store.get('session', hashlib.sha256(request.cookies['cg_session'].encode()).hexdigest())
        session['expires'] = 0
        store.put('session', session)
        response = JSONResponse({'ok': True})
        response.delete_cookie('cg_session')
        return response

    @app.get('/api/state')
    def state(user=Depends(actor)):
        projects, sources, reviews = [], [], []
        for p in store.all('project', user['workspace']):
            try:
                projects.append(service.project(user, p['id']))
            except Rejected:
                pass
        for s in store.all('source', user['workspace']):
            try:
                sources.append(service.source(user, s['id']))
            except Rejected:
                pass
        for r in store.all('review', user['workspace']):
            try:
                checked = service.get_review(user, r['id'])
                reviews.append({k: checked[k] for k in ('id', 'project_id', 'goal', 'readiness', 'created', 'stale', 'test_mode')})
            except Rejected:
                pass
        return {'actor': service.public_user(user), 'users': [service.public_user(u) for u in store.all('user', user['workspace'])],
                'projects': projects, 'sources': sources, 'unknown': service.visible_evidence(user, unknown=True), 'reviews': reviews,
                'connections': {'vexa': 'Configured, live unverified' if (os.getenv('VEXA_API_KEY') or os.getenv('VEXA_BOT_KEY') or os.getenv('VEXA_TX_KEY')) else 'Not configured; contract tests only',
                                'slack': 'OAuth / selected pull client; live unverified',
                                'whatsapp': 'Test/manual import only; live Baileys pairing disabled'},
                'privacy': 'Local records are stored on this computer. Explicit live analysis sends selected evidence and prior decisions to external model providers. Vexa and Slack operations contact their services.'}

    @app.get('/api/projects/{project_id}/evidence')
    def evidence(project_id: str, user=Depends(actor)):
        return {'evidence': service.visible_evidence(user, project_id), 'decisions': service.decisions(user, project_id)}

    @app.get('/api/evidence/{evidence_id}/original')
    def original(evidence_id: str, user=Depends(actor)):
        e = service.entity(user, 'evidence', evidence_id)
        service.source(user, e['source_id'])
        return service.entity(user, 'source_event', e['event_id'])

    @app.get('/api/reviews/{review_id}')
    def review(review_id: str, user=Depends(actor)):
        return service.get_review(user, review_id)

    @app.get('/api/reviews/{review_id}/brief')
    def brief(review_id: str, user=Depends(actor)):
        return PlainTextResponse(service.brief(user, review_id), headers={'Content-Disposition': 'attachment; filename="context-gap-report.md"'})

    def source_failure(user, source_id, exc):
        source = service.source(user, source_id)
        source['last_error'] = str(exc)
        source['retry_after'] = getattr(exc, 'retry_after', None)
        store.put('source', source)

    @app.post('/api/upload')
    async def upload(source_id: str = Form(...), project_id: str = Form(''), consent: bool = Form(False),
                     file: UploadFile = File(...), user=Depends(actor)):
        source = service.source(user, source_id)
        require(source['type'] in {'manual', 'whatsapp'}, 'Use the source-specific connector.')
        require(consent, 'Confirm you may process the document.', 403)
        content = await file.read(4 * 1024 * 1024 + 1)
        try:
            passages = manual(file.filename or 'document.txt', content)
        except AdapterFailure as exc:
            source_failure(user, source_id, exc)
            passages = [Passage(item_id='parse-error-' + ident(), text='', location=(file.filename or 'Upload')[:150],
                                details={'document_name': Path((file.filename or 'document.txt').replace('\\', '/')).name[:150]},
                                extraction='failed', uncertainty=str(exc))]
        with store.transaction():
            rows = service.ingest(user, {'source_id': source_id, 'project_id': project_id or None, 'consent': True,
                                        'passages': [p.model_dump(mode='json') for p in passages],
                                        'original': {'filename': file.filename, 'text_passages': [p.text for p in passages]}})
            if all(p.extraction == 'complete' for p in passages):
                filename = passages[0].details['document_name']
                present = {p.item_id for p in passages}
                for old in store.all('evidence', user['workspace']):
                    if old['source_id'] == source_id and old['active'] and old['details'].get('document_name') == filename and old['item_id'] not in present:
                        if old['project_id']:
                            service.project(user, old['project_id'])
                        old.update(active=False, availability='not_in_new_document_snapshot')
                        store.put('evidence', old)
                if not any(e['active'] and e['source_id'] == source_id and e['extraction'] == 'failed' for e in store.all('evidence', user['workspace'])):
                    source.pop('last_error', None)
                    store.put('source', source)
        return {'evidence': rows}

    def slack_credentials(user):
        credential = store.get('credential', 'slack-' + user['workspace'])
        if credential:
            require(not credential.get('disabled'), 'Slack is disconnected locally. Reconnect through OAuth.', 409)
            try:
                return transform(credential['protected'], decrypt=True), credential['team']
            except RuntimeError:
                raise Rejected('OAuth token could not be unlocked by this Windows account.', 409)
        require(os.getenv('SLACK_BOT_TOKEN') and os.getenv('SLACK_TEAM_ID'), 'Connect Slack through OAuth or configure a scoped token locally.', 409)
        return os.environ['SLACK_BOT_TOKEN'], os.environ['SLACK_TEAM_ID']

    @app.post('/api/command')
    def command(cmd: Command, user=Depends(actor)):
        p, action = cmd.payload, cmd.action
        try:
            if action == 'project':
                return service.create_project(user, p['name'])
            if action == 'user':
                return service.create_user(p['username'], p['password'], user)
            if action == 'member':
                return service.member(user, p['project_id'], p['user_id'], p['role'])
            if action == 'responsibility':
                return service.responsibility(user, p['project_id'], p['topic'], p['user_id'])
            if action == 'source':
                return service.create_source(user, p['type'], p['container'], p['label'], p.get('allowed_users'))
            if action == 'mapping':
                return service.map_source(user, p['source_id'], p['project_id'])
            if action == 'source_grants':
                return service.source_grants(user, p['source_id'], p['allowed_users'])
            if action == 'ingest':
                source = service.source(user, p['source_id'])
                require(source['type'] == 'manual', 'Use the source-specific importer for external event formats.')
                return service.ingest(user, p)
            if action == 'route':
                return service.route(user, p['evidence_id'], p.get('project_id'), p.get('action', 'assign'))
            if action == 'segment':
                return service.segment(user, p['evidence_id'], p['project_id'], p['quote'])
            if action == 'suggestions':
                return service.suggestions(user, p['evidence_id'])
            if action == 'model_suggestions':
                return service.model_suggestions(user, p['evidence_id'], p.get('consent', False))
            if action == 'analyze':
                for key in ('start', 'end'):
                    if p.get(key):
                        date.fromisoformat(p[key])
                return service.analyze(user, p['project_id'], p['goal'], p['source_ids'], p.get('start'), p.get('end'), p.get('consent', False), p.get('test_mode', False))
            if action == 'assign':
                return service.assign(user, p['review_id'], p['finding_id'], p.get('assignee_id'), p.get('collaborators'), p.get('watchers'))
            if action == 'respond':
                return service.respond(user, p['review_id'], p['finding_id'], p['answer'], p.get('citations'), p.get('answer_known', True))
            if action == 'confirm':
                return service.confirm(user, p['review_id'], p['finding_id'], p.get('supersedes'))
            if action == 'dismiss':
                return service.dismiss(user, p['review_id'], p['finding_id'], p['reason'])
            if action == 'demo':
                return demo(user)
            if action == 'slack_disconnect':
                owner(user)
                store.put('credential', {'id': 'slack-' + user['workspace'], 'workspace': user['workspace'], 'disabled': True})
                return {'note': 'Local Slack access disabled. Revoke the app in Slack settings to invalidate its external token.'}
            if action == 'baileys_test':
                source = service.source(user, p['source_id'])
                require(source['type'] == 'whatsapp' and p.get('consent') is True, 'Select an authorized WhatsApp source and confirm processing.')
                passages = baileys_events(p['events'], source['container'])
                return service.ingest(user, {'source_id': source['id'], 'consent': True, 'test_mode': True,
                    'project_id': p.get('project_id'), 'passages': [x.model_dump(mode='json') for x in passages],
                    'original': {'selected_events': [e for e in p['events'] if e.get('key', {}).get('remoteJid') == source['container']]}})
            if action in {'vexa_join', 'vexa_stop', 'vexa_fetch', 'slack_fetch'}:
                source = service.source(user, p['source_id'])
                require(p.get('consent') is True, 'Confirm authorization and external service processing.', 403)
                if p.get('project_id'):
                    service.project(user, p['project_id'])
                try:
                    if action.startswith('vexa_'):
                        require(source['type'] == 'vexa', 'Select a Vexa meeting source.')
                        require(os.getenv('VEXA_API_KEY') or os.getenv('VEXA_BOT_KEY') or os.getenv('VEXA_TX_KEY'),
                                'Vexa key is not configured.', 409)
                        platform, meeting_id = source['container'].split(':', 1)
                        client = Vexa(os.getenv('VEXA_BASE_URL', 'https://api.cloud.vexa.ai'), os.getenv('VEXA_API_KEY'),
                                      bot_key=os.getenv('VEXA_BOT_KEY'), tx_key=os.getenv('VEXA_TX_KEY'))
                        if action == 'vexa_join':
                            return client.join(platform, meeting_id, True, p.get('passcode'))
                        if action == 'vexa_stop':
                            return client.stop(platform, meeting_id)
                        passages, raw = client.fetch(platform, meeting_id)
                    else:
                        owner(user)
                        require(source['type'] == 'slack', 'Select a Slack source.')
                        token, team = slack_credentials(user)
                        selected_team, channel = source['container'].split(':', 1)
                        require(team == selected_team, 'Selected workspace does not match the authorized token.', 403)
                        passages, raw = Slack(token, team).fetch(channel, p.get('thread'), p.get('oldest'), p.get('latest'))
                        if raw['complete']:
                            # Reconcile only the exact selected channel/thread/time window after a complete pull.
                            present = {x.item_id for x in passages}
                            for e in service.visible_evidence(user):
                                if e['source_id'] != source['id'] or e.get('parent_id') or e['deleted']:
                                    continue
                                if p.get('thread') and e['details'].get('thread_ts') != p['thread'] and e['item_id'] != p['thread']:
                                    continue
                                if not p.get('thread') and e['details'].get('thread_ts') and e['details']['thread_ts'] != e['item_id']:
                                    continue  # Channel history does not enumerate thread replies.
                                if (p.get('oldest') and float(e['item_id']) < float(p['oldest'])) or (p.get('latest') and float(e['item_id']) > float(p['latest'])):
                                    continue
                                if e['item_id'] not in present:
                                    passages.append(Passage(item_id=e['item_id'], text='', location=e['location'],
                                        details={**e['details'], 'availability': 'not_returned'}, extraction='partial',
                                        uncertainty='Not returned by the complete selected pull. Deletion is not proven; retention/access may differ.'))
                    if not passages:
                        raise AdapterFailure('Selected source has no text in this range. No content was invented.')
                    result = service.ingest(user, {'source_id': source['id'], 'project_id': p.get('project_id'), 'consent': True,
                                                    'passages': [x.model_dump(mode='json') for x in passages], 'original': raw})
                    source.pop('last_error', None)
                    store.put('source', source)
                    return result
                except AdapterFailure as exc:
                    source_failure(user, source['id'], exc)
                    raise Rejected(str(exc), 409)
            raise Rejected('Unknown command.')
        except (KeyError, TypeError, AttributeError, ValueError):
            raise Rejected('Invalid command fields. Check the form values and limits.') from None

    def demo(user):
        project = service.create_project(user, 'Orchid — fictional pilot')
        texts = [(ROOT / 'samples' / f).read_text(encoding='utf-8') for f in ('01-brief.md', '02-spec.md', '03-notes.md')]
        sources = []
        for index, text in enumerate(texts):
            source = service.create_source(user, 'manual', 'demo-' + project['id'] + '-' + str(index), f'Fictional document {index + 1}')
            passages = manual(f'fictional-{index + 1}.md', text.encode())
            service.ingest(user, {'source_id': source['id'], 'project_id': project['id'], 'consent': True, 'test_mode': True,
                                 'passages': [p.model_dump(mode='json') for p in passages], 'original': {'filename': f'fictional-{index + 1}.md', 'text': text}})
            sources.append(source['id'])
        return {'project': project, 'source_ids': sources}

    @app.post('/api/slack/connect')
    def slack_connect(request: Request, user=Depends(actor)):
        owner(user)
        require(os.getenv('SLACK_CLIENT_ID') and os.getenv('SLACK_CLIENT_SECRET'), 'Configure Slack OAuth client settings locally.', 409)
        state = secrets.token_urlsafe(32)
        store.put('oauth_state', {'id': hashlib.sha256(state.encode()).hexdigest(), 'workspace': user['workspace'],
                                 'actor': user['id'], 'session': hashlib.sha256(request.cookies['cg_session'].encode()).hexdigest(),
                                 'expires': time.time() + 600, 'used': False})
        response = JSONResponse({'url': 'https://slack.com/oauth/v2/authorize?' + urlencode({'client_id': os.environ['SLACK_CLIENT_ID'],
                   'scope': 'channels:read,channels:history', 'redirect_uri': os.getenv('SLACK_REDIRECT_URI', 'http://127.0.0.1:8027/api/slack/callback'), 'state': state})})
        response.set_cookie('cg_oauth', state, httponly=True, samesite='lax', max_age=600)
        return response

    @app.get('/api/slack/callback')
    def slack_callback(request: Request, state: str = '', code: str = ''):
        key = hashlib.sha256(state.encode()).hexdigest()
        with store.transaction():
            saved = store.get('oauth_state', key)
            require(state and request.cookies.get('cg_oauth') == state and saved and saved['expires'] > time.time()
                    and not saved['used'], 'OAuth state is invalid or expired.', 403)
            session = store.get('session', saved['session'])
            require(session and session['expires'] > time.time(), 'Original login expired; reconnect Slack.', 403)
            user = store.get('user', saved['actor'])
            owner(user)
            saved['used'] = True
            store.put('oauth_state', saved)
        try:
            with httpx.Client(timeout=20, trust_env=False) as client:
                result = client.post('https://slack.com/api/oauth.v2.access', data={'client_id': os.getenv('SLACK_CLIENT_ID'),
                    'client_secret': os.getenv('SLACK_CLIENT_SECRET'), 'code': code,
                    'redirect_uri': os.getenv('SLACK_REDIRECT_URI', 'http://127.0.0.1:8027/api/slack/callback')})
                result.raise_for_status()
                payload = result.json()
            require(payload.get('ok') and payload.get('access_token') and payload.get('team', {}).get('id'), 'Slack OAuth was not authorized.', 409)
            protected = transform(payload['access_token'])
            store.put('credential', {'id': 'slack-' + user['workspace'], 'workspace': user['workspace'], 'protected': protected,
                                     'team': payload['team']['id'], 'scope': payload.get('scope', '')})
        except (httpx.HTTPError, ValueError, RuntimeError):
            raise Rejected('Slack OAuth failed or Windows token protection is unavailable. No plaintext token was saved.', 409) from None
        response = RedirectResponse('/?slack=connected', status_code=303)
        response.delete_cookie('cg_oauth')
        return response

    app.mount('/static', StaticFiles(directory=ROOT / 'web'), name='static')

    @app.get('/')
    def index():
        return FileResponse(ROOT / 'web/index.html')

    return app
