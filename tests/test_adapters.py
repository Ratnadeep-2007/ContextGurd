import io

import httpx
import pytest

from app.adapters import AdapterFailure, Slack, Vexa, baileys_events, manual


def test_manual_text_and_docx():
    from docx import Document
    assert len(manual('notes.md', b'First paragraph.\n\nSecond paragraph.')) == 2
    doc = Document()
    doc.core_properties.author = 'Fictional author'
    doc.add_paragraph('Orchid source statement.')
    output = io.BytesIO()
    doc.save(output)
    parsed = manual('brief.docx', output.getvalue())[0]
    assert parsed.text == 'Orchid source statement.' and parsed.author == 'Fictional author'


def test_manual_failure_and_limits():
    for name, content in [('x.exe', b'text'), ('bad.pdf', b'bad pdf'), ('bad.txt', b'\xff'), ('empty.md', b'')]:
        with pytest.raises(AdapterFailure):
            manual(name, content)


def test_vexa_join_consent_and_partial_transcript():
    calls = []
    def handle(req):
        calls.append(req.method)
        if req.method == 'POST':
            return httpx.Response(200, json={'status': 'requested'})
        return httpx.Response(200, json={'status': 'active', 'segments': [{'segment_id': 's1', 'start': 1, 'end': 3,
                                           'text': 'Pilot discussion', 'speaker': '', 'completed': False}]})
    vexa = Vexa('https://vexa.example', 'test-key', httpx.MockTransport(handle))
    with pytest.raises(AdapterFailure):
        vexa.join('google_meet', 'abc-defg-hij', False)
    assert not calls
    assert vexa.join('google_meet', 'abc-defg-hij', True)['status'] == 'requested'
    passages, original = vexa.fetch('google_meet', 'abc-defg-hij')
    assert passages[0].author is None and passages[0].extraction == 'partial'
    assert passages[0].item_id == 's1'


def test_vexa_missing_transcript():
    v = Vexa('https://vexa.example', 'test', httpx.MockTransport(lambda req: httpx.Response(200, json={'segments': []})))
    with pytest.raises(AdapterFailure):
        v.fetch('zoom', '12345678901')


def test_slack_selected_team_channel_and_revision():
    def handle(req):
        method = req.url.path.rsplit('/', 1)[-1]
        if method == 'auth.test':
            return httpx.Response(200, json={'ok': True, 'team_id': 'T1'})
        if method == 'conversations.info':
            return httpx.Response(200, json={'ok': True})
        if method == 'chat.getPermalink':
            return httpx.Response(200, json={'ok': True, 'permalink': 'https://example.slack.com/archives/C11/p123'})
        assert req.url.params['channel'] == 'C11'
        return httpx.Response(200, json={'ok': True, 'messages': [{'ts': '1700000000.000001', 'text': 'Updated statement.', 'user': 'U1', 'edited': {'ts': '1700000010.0'}}]})
    slack = Slack('test', 'T1', httpx.MockTransport(handle))
    passages, original = slack.fetch('C11')
    assert original['complete'] and passages[0].details['edited'] and passages[0].external_identity == 'U1'
    slack.team = 'T2'
    with pytest.raises(AdapterFailure):
        slack.fetch('C11')


def test_slack_rate_limit_and_revocation():
    slack = Slack('test', 'T1', httpx.MockTransport(lambda r: httpx.Response(429, headers={'Retry-After': '30'})))
    with pytest.raises(AdapterFailure) as exc:
        slack.fetch('C11')
    assert exc.value.retry_after == '30'
    revoked = Slack('test', 'T1', httpx.MockTransport(lambda r: httpx.Response(200, json={'ok': False, 'error': 'token_revoked'})))
    with pytest.raises(AdapterFailure, match='token_revoked'):
        revoked.fetch('C11')


def test_baileys_discards_other_chats_and_has_no_send_capability():
    events = [{'key': {'remoteJid': 'selected@g.us', 'id': 'x'}, 'message': {'conversation': 'Selected passage.'}},
              {'key': {'remoteJid': 'private@g.us', 'id': 'y'}, 'message': {'conversation': 'Private content.'}}]
    assert [p.text for p in baileys_events(events, 'selected@g.us')] == ['Selected passage.']
