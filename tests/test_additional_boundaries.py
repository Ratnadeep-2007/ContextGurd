import pytest

from app.contracts import RoutingProposal
from app.review import Reviews
from app.service import Rejected
from test_routing import env, ingest
from test_review import setup


def test_model_suggestions_filter_candidates_and_never_route(env):
    s, a, b, p, q, source = env
    s.member(a, p['id'], b['id'], 'reviewer')
    s.source_grants(a, source['id'], [b['id']])
    e = ingest(env)
    class Suggest:
        def suggest(self, passage, candidates):
            assert [x['id'] for x in candidates] == [p['id']]
            return RoutingProposal(suggestions=[{'project_id': p['id'], 'reason': 'Name matches the passage.', 'uncertainty': 'Still needs human confirmation.'}]), 'Controlled'
    r = Reviews(s.store, Suggest())
    result = r.model_suggestions(b, e['id'], True)
    assert result['suggestions'][0]['confirmed'] is False
    assert s.store.get('evidence', e['id'])['routing'] == 'unknown'
    with pytest.raises(Rejected):
        r.model_suggestions(b, e['id'], False)


def test_revoked_source_access_blocks_report_and_memory(env):
    r, a, b, p, q, source, rows, review = setup(env)
    f = review['findings'][0]
    r.respond(a, review['id'], f['id'], 'Use January 18.')
    r.confirm(a, review['id'], f['id'])
    assert r.get_review(b, review['id'])
    r.source_grants(a, source['id'], [])
    with pytest.raises(Rejected):
        r.get_review(b, review['id'])
    assert not r.decisions(b, p['id'])


def test_deleted_source_invalidates_review_and_original_is_preserved(env):
    r, a, b, p, q, source, rows, review = setup(env)
    old = rows[0]
    tombstone = r.ingest(a, {'source_id': source['id'], 'consent': True, 'test_mode': True,
                            'passages': [{'item_id': old['item_id'], 'text': '', 'deleted': True}]})[0]
    assert tombstone['deleted'] and r.get_review(a, review['id'])['stale']
    assert r.store.get('evidence', old['id'])['text'] == old['text']


def test_document_identity_and_duplicate_sources(env):
    from app.adapters import manual
    s, a, b, p, q, source = env
    assert s.create_source(a, 'manual', source['container'], 'Another label')['id'] == source['id']
    assert manual('one.md', b'Same passage.')[0].item_id != manual('two.md', b'Same passage.')[0].item_id


def test_pdf_text_page_reference():
    # Minimal self-authored text PDF; no pre-existing document or application fixture.
    from app.adapters import manual
    stream = b'BT /F1 12 Tf 20 100 Td (Fictional pilot source.) Tj ET'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Count 1 /Kids [3 0 R] >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>', b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream']
    pdf = b'%PDF-1.4\n'; offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(pdf)); pdf += f'{i} 0 obj\n'.encode() + obj + b'\nendobj\n'
    xref = len(pdf)
    pdf += b'xref\n0 6\n0000000000 65535 f \n' + b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
    pdf += f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode()
    result = manual('sample.pdf', pdf)
    assert 'page 1' in result[0].location and 'Fictional pilot source.' in result[0].text


def test_stale_segments_cannot_enter_new_review(env):
    s, a, b, p, q, source = env
    e = ingest(env)
    s.segment(a, e['id'], p['id'], 'pilot starts on January 18.')
    ingest(env, passages=[{'item_id': 'one', 'text': 'New schedule replaces the old passage.'}])
    r = Reviews(s.store)
    review = r.analyze(a, p['id'], 'Check pilot readiness', [source['id']], test_mode=True)
    assert not review['evidence'] and review['status'] == 'failed'


def test_strict_boolean_and_response_citation(env):
    r, a, b, p, q, source, rows, review = setup(env)
    f = review['findings'][0]
    with pytest.raises(Rejected):
        r.respond(a, review['id'], f['id'], 'Unknown answer', answer_known='false')
    with pytest.raises(Rejected):
        r.respond(a, review['id'], f['id'], 'Some answer', citations=[{'evidence_id': rows[0]['id'], 'quote': ''}])
    with pytest.raises(Rejected):
        r.analyze(a, p['id'], 'Check readiness', [source['id']], consent='false')


def test_source_grant_cannot_read_or_revise_an_inaccessible_project(env):
    s, a, b, p, q, source = env
    e = ingest(env, project_id=p['id'])
    s.source_grants(a, source['id'], [b['id']])
    for text in (e['text'], 'Changed confidential statement.'):
        with pytest.raises(Rejected):
            s.ingest(b, {'source_id': source['id'], 'consent': True, 'passages': [{'item_id': 'one', 'text': text}]})
    assert s.store.get('evidence', e['id'])['active']
