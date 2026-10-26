"""UI-facing capture and connection endpoints; legacy adapters stay isolated."""
import json
import os
import hashlib
import base64
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from fastapi import Depends, File, Form, UploadFile
from fastapi.responses import PlainTextResponse, Response
from pydantic import Field

from .adapters import AdapterFailure, Slack, Vexa, manual, meeting_link
from .contracts import Contract, Passage
from .exports import consolidated, docx_bytes
from .service import Rejected, digest, now, require


class Capture(Contract):
    text: str = Field(min_length=1, max_length=60000)
    label: str = Field(default='Conversation notes', min_length=1, max_length=120)
    source_type: Literal['manual', 'whatsapp'] = 'manual'
    project_ids: list[str] | None = None
    goal: str = Field(default='', max_length=1500)
    consent: bool = Field(default=False, strict=True)
    model_consent: bool = Field(default=False, strict=True)
    test_mode: bool = Field(default=False, strict=True)
    share: bool = Field(default=False, strict=True)


class Meeting(Contract):
    link: str = Field(min_length=12, max_length=2000)
    operation: Literal['join', 'stop', 'fetch']
    passcode: str = Field(default='', max_length=200)
    consent: bool = Field(default=False, strict=True)
    model_consent: bool = Field(default=False, strict=True)
    project_ids: list[str] | None = None
    share: bool = Field(default=False, strict=True)


class SlackSelection(Contract):
    channel: str = Field(min_length=3, max_length=40)
    thread: str | None = Field(default=None, max_length=40)
    start: str | None = None
    end: str | None = None
    consent: bool = Field(default=False, strict=True)
    model_consent: bool = Field(default=False, strict=True)
    project_ids: list[str] | None = None
    share: bool = Field(default=False, strict=True)


class WhatsAppConsent(Contract):
    consent: bool = Field(default=False, strict=True)


class WhatsAppChats(WhatsAppConsent):
    ids: list[str] = Field(default_factory=list, max_length=20)


class WhatsAppCapture(WhatsAppConsent):
    project_ids: list[str] | None = None
    model_consent: bool = Field(default=False, strict=True)
    share: bool = Field(default=False, strict=True)
    goal: str = Field(default='', max_length=1500)


def connection_summary(store, user, whatsapp=None):
    slack = store.get('credential', 'slack-' + user['workspace'])
    local_ready = bool(os.getenv('SLACK_BOT_TOKEN') and os.getenv('SLACK_TEAM_ID'))
    flags = {
        'vexa': bool(os.getenv('VEXA_BOT_KEY') or os.getenv('VEXA_TX_KEY') or os.getenv('VEXA_API_KEY')),
        'slack': bool((slack and not slack.get('disabled') and (slack.get('mode') != 'env' or local_ready)) or (not slack and local_ready)),
        'whatsapp': False,
    }
    output = {}
    for name, configured in flags.items():
        checked = store.get('connection_check', 'connection-' + user['workspace'] + '-' + name)
        output[name] = {'configured': configured, 'status': 'Configured; not checked' if configured else 'Not connected',
                        'checked_at': checked.get('checked_at') if checked else None,
                        'last_check': checked.get('status') if checked else None}
        if configured and checked and 'ok' in checked:
            output[name]['status'] = 'Connected' if checked['ok'] else 'Connection failed'
    output['whatsapp'] = whatsapp.summary(user['workspace']) if whatsapp and user['role'] == 'owner' else {
        'configured': False, 'status': 'Admin manages live pairing; manual import available', 'selected': [], 'chats': []}
    output['slack']['local_token_ready'] = local_ready
    output['slack']['oauth_ready'] = bool(os.getenv('SLACK_CLIENT_ID') and os.getenv('SLACK_CLIENT_SECRET'))
    return output


def install(app, service, store, actor, owner, slack_credentials, workers):
    def schedule(user, payload):
        job, created = service.create_intake(user, payload)
        if created:
            workers.submit(service.process_intake, job['id'])
        return service.intake(user, job['id'])

    def root_source(user, source_type, label, identity):
        return service.create_source(user, source_type, 'capture:' + digest({'actor': user['id'], 'identity': identity}), label)

    @app.post('/api/whatsapp/connect')
    def whatsapp_connect(payload: WhatsAppConsent, user=Depends(actor)):
        owner(user)
        require(payload.consent, 'Confirm authorization before linking your WhatsApp device.', 403)
        return app.state.whatsapp.call(user['workspace'], 'connect')

    @app.get('/api/whatsapp/status')
    def whatsapp_status(user=Depends(actor)):
        owner(user)
        return app.state.whatsapp.summary(user['workspace'])

    @app.get('/api/whatsapp/qr')
    def whatsapp_qr(user=Depends(actor)):
        owner(user)
        result = app.state.whatsapp.call(user['workspace'], 'qr')
        return Response(base64.b64decode(result['png'], validate=True), media_type='image/png')

    @app.post('/api/whatsapp/chats')
    def whatsapp_chats(user=Depends(actor)):
        owner(user)
        return app.state.whatsapp.call(user['workspace'], 'chats')

    @app.post('/api/whatsapp/select')
    def whatsapp_select(payload: WhatsAppChats, user=Depends(actor)):
        owner(user)
        require(payload.consent, 'Confirm permission to collect text from these selected chats.', 403)
        import re
        require(all(re.fullmatch(r'\d+(?:-\d+)?@(?:g\.us|s\.whatsapp\.net|lid)', value) for value in payload.ids), 'Select valid chat IDs.')
        return app.state.whatsapp.call(user['workspace'], 'select', {'ids': payload.ids})

    @app.post('/api/whatsapp/disconnect')
    def whatsapp_disconnect(user=Depends(actor)):
        owner(user)
        return app.state.whatsapp.disconnect(user['workspace'])

    @app.post('/api/whatsapp/capture', status_code=202)
    def whatsapp_capture(payload: WhatsAppCapture, user=Depends(actor)):
        owner(user)
        require(payload.consent and payload.model_consent, 'Authorize selected chat processing and external model access.', 403)
        service.candidate_projects(user, payload.project_ids)
        summary = app.state.whatsapp.summary(user['workspace'])
        selected = set(summary.get('selected', []))
        require(summary.get('status') == 'connected' and selected, 'Connect WhatsApp and select chats first.', 409)
        rows = app.state.whatsapp.call(user['workspace'], 'messages')['messages']
        require(rows and all(row.get('chat') in selected for row in rows), 'No selected chat text is ready, or the selection changed.', 409)
        require(len(rows) <= 300 and sum(len(row['text']) for row in rows) <= 60000, 'Selected text exceeds processing limits.', 409)
        grouped = {}
        for row in rows:
            grouped.setdefault(row['chat'], []).append(Passage(item_id=row['message_id'], text=row['text'],
                author=row.get('author'), external_identity=row.get('external_identity'), timestamp=row.get('timestamp'),
                location='WhatsApp chat ' + row['chat'] + ', message ' + row['message_id'],
                details={'chat_id': row['chat'], 'message_id': row['message_id'], 'from_me': row.get('from_me', False),
                         'account_id': summary.get('account_id'), 'collecting_since': summary.get('collecting_since'),
                         'coverage': 'Selected live text received since collection began; no historical sync.'}))
        sources = []
        for chat, passages in grouped.items():
            source = service.create_source(user, 'whatsapp', 'live:' + digest({'workspace': user['workspace'],
                'account': summary.get('account_id'), 'chat': chat}), 'WhatsApp - ' + chat)
            sources.append({'source_id': source['id'], 'passages': [p.model_dump(mode='json') for p in passages]})
        job = schedule(user, {**payload.model_dump(), 'sources': sources})
        # Clear only the exact queued revisions, keeping edits/new arrivals for the next batch.
        try:
            app.state.whatsapp.call(user['workspace'], 'ack', {'items': [{'id': row['id'], 'revision': row['revision']} for row in rows]})
        except Rejected:
            pass  # The queued intake is durable; duplicate retries are deduplicated.
        return job

    @app.post('/api/intakes/text', status_code=202)
    def capture(payload: Capture, user=Depends(actor)):
        require(payload.consent, 'Confirm authorization before processing.', 403)
        service.candidate_projects(user, payload.project_ids)
        source = root_source(user, payload.source_type, payload.label, {'label': payload.label, 'text': payload.text})
        return schedule(user, {**payload.model_dump(exclude={'text', 'label', 'source_type'}), 'sources': [{
            'source_id': source['id'], 'passages': [Passage(item_id='text', text=payload.text,
                location=payload.label, author=user['username']).model_dump(mode='json')]}]})

    @app.post('/api/intakes/upload', status_code=202)
    async def upload(files: list[UploadFile] = File(...), project_ids: str = Form(''), goal: str = Form(''),
                     source_type: str = Form('manual'), consent: bool = Form(False), model_consent: bool = Form(False),
                     test_mode: bool = Form(False), share: bool = Form(False), user=Depends(actor)):
        require(consent, 'Confirm authorization before uploading.', 403)
        require(source_type in {'manual', 'whatsapp'} and 1 <= len(files) <= 8, 'Select up to eight supported files.')
        try:
            selected = json.loads(project_ids) if project_ids else None
            require(selected is None or isinstance(selected, list), 'Invalid project selection.')
            service.candidate_projects(user, selected)
            parsed = []
            for file in files:
                content = await file.read(4 * 1024 * 1024 + 1)
                name = Path((file.filename or 'document.txt').replace('\\', '/')).name[:120]
                try:
                    passages = manual(name, content)
                except AdapterFailure as exc:
                    raise Rejected(name + ': ' + str(exc), 400) from None
                parsed.append((name, content, passages))
            sources = []
            require(len({name.casefold() for name, _, _ in parsed}) == len(parsed), 'Use distinct filenames within one upload batch.')
            for name, content, passages in parsed:
                source = root_source(user, source_type, name, {'name': name.casefold(), 'type': source_type,
                                     'content': hashlib.sha256(content).hexdigest()})
                sources.append({'source_id': source['id'], 'passages': [p.model_dump(mode='json') for p in passages]})
            return schedule(user, {'sources': sources, 'project_ids': selected, 'goal': goal, 'consent': consent,
                                  'model_consent': model_consent, 'test_mode': test_mode, 'share': share})
        except (AdapterFailure, ValueError) as exc:
            raise Rejected(str(exc) if isinstance(exc, AdapterFailure) else 'Invalid upload fields.', 400) from None

    @app.get('/api/intakes/{job_id}')
    def status(job_id: str, user=Depends(actor)):
        return service.intake(user, job_id)

    @app.post('/api/intakes/{job_id}/retry', status_code=202)
    def retry(job_id: str, user=Depends(actor)):
        job = service.retry_intake(user, job_id)
        workers.submit(service.process_intake, job_id)
        return job

    @app.get('/api/reviews')
    def reviews(project_id: str = '', source_id: str = '', start: str = '', end: str = '', status: str = 'all', user=Depends(actor)):
        require(status in {'all', 'open', 'recorded', 'failed'}, 'Invalid review status filter.')
        try:
            if start:
                date.fromisoformat(start)
            if end:
                date.fromisoformat(end)
            require(not start or not end or start <= end, 'The start date must precede the end date.')
        except ValueError:
            raise Rejected('Use valid dates.') from None
        if project_id:
            service.project(user, project_id)
        if source_id:
            service.source(user, source_id)
        result = []
        for row in store.all('review', user['workspace']):
            try:
                review = service.get_review(user, row['id'])
            except Rejected:
                continue
            if project_id and review['project_id'] != project_id:
                continue
            if source_id and source_id not in review['source_ids'] and not any(e['details'].get('origin_source_id') == source_id for e in review['evidence']):
                continue
            stamp = review['created'][:10]
            if (start and stamp < start) or (end and stamp > end):
                continue
            open_count = sum(f['state'] == 'open' and f['kind'] != 'verified_fact' for f in review['findings'])
            if status == 'open' and not open_count or status == 'recorded' and (open_count or review['status'] != 'complete') or status == 'failed' and review['status'] != 'failed':
                continue
            result.append({k: review[k] for k in ('id', 'project_id', 'goal', 'created', 'readiness', 'stale', 'test_mode', 'status', 'source_ids')} |
                          {'open_count': open_count, 'finding_count': len(review['findings'])})
        return sorted(result, key=lambda r: r['created'], reverse=True)

    @app.get('/api/reviews/{review_id}/document')
    def document(review_id: str, format: str = 'docx', user=Depends(actor)):
        require(format in {'md', 'docx'}, 'Choose Markdown or Word output.')
        text = consolidated(service, user, review_id)
        if format == 'md':
            return PlainTextResponse(text, headers={'Content-Disposition': 'attachment; filename="consolidated-context.md"'})
        return Response(docx_bytes(text), media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        headers={'Content-Disposition': 'attachment; filename="consolidated-context.docx"'})

    def vexa():
        return Vexa(os.getenv('VEXA_BASE_URL', 'https://api.cloud.vexa.ai'), os.getenv('VEXA_API_KEY'),
                    bot_key=os.getenv('VEXA_BOT_KEY'), tx_key=os.getenv('VEXA_TX_KEY'))

    @app.post('/api/slack/local-connect')
    def local_slack(user=Depends(actor)):
        owner(user)
        require(os.getenv('SLACK_BOT_TOKEN') and os.getenv('SLACK_TEAM_ID'), 'Configure a local bot token and workspace ID.', 409)
        try:
            auth = Slack(os.environ['SLACK_BOT_TOKEN'], os.environ['SLACK_TEAM_ID']).call('auth.test')
            require(auth.get('team_id') == os.environ['SLACK_TEAM_ID'], 'Slack workspace does not match the configured token.', 403)
            store.put('credential', {'id': 'slack-' + user['workspace'], 'workspace': user['workspace'],
                                    'mode': 'env', 'disabled': False, 'team': auth['team_id']})
            store.put('connection_check', {'id': 'connection-' + user['workspace'] + '-slack',
                'workspace': user['workspace'], 'status': 'Slack local-token authentication verified.',
                'checked_at': now(), 'ok': True})
            return {'connected': True, 'note': 'Local Slack token verified. Select a channel in Project Reviews.'}
        except AdapterFailure as exc:
            raise Rejected(str(exc), 409) from None

    @app.post('/api/connections/{name}/check')
    def check(name: str, user=Depends(actor)):
        owner(user)
        require(name in {'vexa', 'slack'}, 'Use the WhatsApp pairing controls in Sources.')
        try:
            if name == 'vexa':
                running = vexa().status()
                for source in store.all('source', user['workspace']):
                    if source['type'] != 'vexa' or source['container'].startswith('routed:'):
                        continue
                    platform, native = source['container'].split(':', 1)
                    found = next((b for b in running if b.get('platform') == platform and str(b.get('native_meeting_id')) == native), None)
                    source['last_bot_status'] = (found.get('status') or 'Running; admission not confirmed') if found else 'Not listed as running'
                    store.put('source', source)
                message = 'Vexa bot API reachable; meeting/transcript access requires its own check.'
            else:
                token, team = slack_credentials(user)
                auth = Slack(token, team).call('auth.test')
                require(auth.get('team_id') == team, 'Slack workspace does not match the configured authorization.', 403)
                message = 'Slack authentication verified; channel access is checked when selected.'
            result = {'id': 'connection-' + user['workspace'] + '-' + name, 'workspace': user['workspace'],
                      'status': message, 'checked_at': now(), 'ok': True}
            store.put('connection_check', result)
            return result
        except (AdapterFailure, Rejected) as exc:
            message = exc.message if isinstance(exc, Rejected) else str(exc)
            store.put('connection_check', {'id': 'connection-' + user['workspace'] + '-' + name,
                'workspace': user['workspace'], 'status': message, 'checked_at': now(), 'ok': False})
            raise Rejected(message, exc.status if isinstance(exc, Rejected) else 409) from None

    @app.post('/api/meetings')
    def meeting(payload: Meeting, user=Depends(actor)):
        owner(user)
        require(payload.consent, 'Confirm authorization and inform participants before contacting Vexa.', 403)
        try:
            platform, native_id, embedded = meeting_link(payload.link)
            source = service.create_source(user, 'vexa', platform + ':' + native_id, 'Meeting · ' + native_id)
            client = vexa()
            if payload.operation == 'join':
                result = client.join(platform, native_id, True, payload.passcode or embedded)
            elif payload.operation == 'stop':
                result = client.stop(platform, native_id)
            else:
                passages, _ = client.fetch(platform, native_id)
                require(bool(passages), 'No transcript text is available yet. No review was created.', 409)
                job = schedule(user, {'sources': [{'source_id': source['id'], 'passages': [p.model_dump(mode='json') for p in passages]}],
                    'project_ids': payload.project_ids, 'consent': True, 'model_consent': payload.model_consent, 'share': payload.share})
                return {'job': job, 'note': 'Transcript received. Project reviews are processing.'}
            source.update(operation=payload.operation, operation_status=result['status'], operation_date=now())
            store.put('source', source)
            return result
        except AdapterFailure as exc:
            raise Rejected(str(exc), 409) from None

    @app.get('/api/slack/channels')
    def channels(user=Depends(actor)):
        owner(user)
        token, team = slack_credentials(user)
        client = Slack(token, team)
        try:
            require(client.call('auth.test').get('team_id') == team, 'Slack workspace mismatch.', 403)
            result, cursor = [], ''
            for _ in range(5):
                page = client.call('conversations.list', types='public_channel', exclude_archived='true', limit=200, cursor=cursor)
                result += [{'id': c['id'], 'name': c['name']} for c in page.get('channels', []) if c.get('is_member')]
                cursor = page.get('response_metadata', {}).get('next_cursor', '')
                if not cursor:
                    break
            return {'team': team, 'channels': result, 'complete': not bool(cursor)}
        except AdapterFailure as exc:
            raise Rejected(str(exc), 409) from None

    @app.post('/api/slack/capture', status_code=202)
    def slack_capture(payload: SlackSelection, user=Depends(actor)):
        owner(user)
        require(payload.consent, 'Confirm permission to read this selected channel/thread.', 403)
        token, team = slack_credentials(user)
        try:
            start = str(datetime.fromisoformat(payload.start + 'T00:00:00+00:00').timestamp()) if payload.start else None
            end = str(datetime.fromisoformat(payload.end + 'T23:59:59.999999+00:00').timestamp()) if payload.end else None
            require(not start or not end or float(start) <= float(end), 'The start date must precede the end date.')
            passages, raw = Slack(token, team).fetch(payload.channel, payload.thread, start, end)
            require(raw.get('complete'), 'The selected Slack range exceeds a complete pull. Narrow the dates; no partial review was generated.', 409)
            require(passages, 'No messages in the selected range.', 409)
            source = service.create_source(user, 'slack', team + ':' + payload.channel, 'Slack · ' + payload.channel)
            return schedule(user, {'sources': [{'source_id': source['id'], 'passages': [p.model_dump(mode='json') for p in passages]}],
                'project_ids': payload.project_ids, 'consent': True, 'model_consent': payload.model_consent, 'share': payload.share})
        except AdapterFailure as exc:
            raise Rejected(str(exc), 409) from None
        except ValueError:
            raise Rejected('Use valid dates.') from None

    app.state.schedule_intake = schedule
