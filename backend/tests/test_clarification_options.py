from backend.app.sample import fixture_candidates, sample_case
from backend.app.schemas import AnswerOption
from backend.app.store import Store
from backend.app.workflow import clarification_options, verify
from .conftest import finish


def test_options_must_quote_their_cited_evidence():
    case=sample_case();evidence,candidates=fixture_candidates(case)
    conflict=next(c for c in candidates if c.type=='potential_conflict')
    refs=[e for e in evidence if e.id in conflict.evidence_ids]
    conflict.answer_options=[AnswerOption(text='An invented third release date',evidence_ids=[refs[0].id]),AnswerOption(text='     ',evidence_ids=[refs[0].id]),AnswerOption(text=refs[1].quote,evidence_ids=[refs[1].id])]
    options=clarification_options(conflict,evidence)
    assert len(options)==1 and options[0].text==refs[1].quote


def test_saved_source_choice_preserves_provenance_and_memory(client,sample):
    prefix=f"/api/cases/{sample['id']}"
    finding=next(f for f in sample['report']['findings'] if f['check_id']=='dates')
    assert len(finding['answer_options'])==2
    selected=finding['answer_options'][1]
    response=client.post(prefix+'/resolutions',json={'version':sample['version'],'finding_id':finding['id'],'action':'confirm','option_text':selected['text'],'answer':'Ignore this untrusted extra answer','owner':'Test lead'})
    assert response.status_code==202
    updated=finish(client,sample['id'])
    saved=next(f for f in updated['report']['findings'] if f['id']==finding['id'])
    assert saved['status']=='user_confirmed' and saved['answer']==selected['text']
    assert saved['option_text']==selected['text'] and saved['option_passage_ids']
    history=Store(client.app.state.store.path).get(sample['id']).resolutions[-1]
    assert history.option_text==selected['text'] and history.option_evidence_ids==selected['evidence_ids']
    assert history.option_passage_ids==saved['option_passage_ids']
    brief=client.get(prefix+'/brief').text
    assert '## Recorded clarifications' in brief and 'Selected source statement:' in brief and 'Choice source:' in brief


def test_api_rejects_invented_choice_and_choice_for_nonanswer_action(client,sample):
    prefix=f"/api/cases/{sample['id']}"
    finding=next(f for f in sample['report']['findings'] if f['check_id']=='dates')
    request={'version':sample['version'],'finding_id':finding['id'],'action':'confirm','option_text':'Made-up choice that is not offered'}
    assert client.post(prefix+'/resolutions',json=request).status_code==400
    request.update(action='dismiss',option_text=finding['answer_options'][0]['text'],answer='Does not apply')
    assert client.post(prefix+'/resolutions',json=request).status_code==400


def test_all_clarified_brief_contains_decisions_and_remaining_limits(client,sample):
    prefix=f"/api/cases/{sample['id']}";case=sample
    for finding in sample['report']['findings']:
        response=client.post(prefix+'/resolutions',json={'version':case['version'],'finding_id':finding['id'],'action':'confirm','answer':'Synthetic test clarification for this question.'})
        assert response.status_code==202
        case=finish(client,case['id'])
    brief=client.get(prefix+'/brief').text
    assert 'User-confirmed clarifications: 4' in brief and 'Still unanswered: 0' in brief
    assert 'All listed findings have a recorded answer' in brief
    assert '## Limitations' in brief and 'Final decisions remain with the project lead' in brief


def test_missing_information_does_not_invent_answer_choices():
    case=sample_case();evidence,candidates=fixture_candidates(case)
    report=verify(case,case.criteria,evidence,candidates)
    missing=next(f for f in report.findings if f.type=='missing_information')
    assert missing.answer_options==[]


def test_dropdown_choice_records_source_and_choice_identity(client,sample):
    prefix=f"/api/cases/{sample['id']}"
    finding=next(f for f in sample['report']['findings'] if f['check_id']=='dates')
    choice=next(c for c in finding['clarification_choices'] if c['kind']=='source')
    response=client.post(prefix+'/resolutions',json={'version':sample['version'],'finding_id':finding['id'],'action':choice['action'],'choice_id':choice['id'],'answer':'An extra answer must not override the selected choice.'})
    assert response.status_code==202
    updated=finish(client,sample['id'])
    saved=next(f for f in updated['report']['findings'] if f['id']==finding['id'])
    assert saved['answer']==choice['answer'] and saved['choice_id']==choice['id']
    assert saved['option_text']==choice['answer'] and saved['option_passage_ids']
    assert updated['resolutions'][-1]['choice_id']==choice['id']


def test_missing_information_dropdown_can_keep_question_open(client,sample):
    prefix=f"/api/cases/{sample['id']}"
    finding=next(f for f in sample['report']['findings'] if f['type']=='missing_information')
    choice=next(c for c in finding['clarification_choices'] if c['id']=='keep_open')
    assert 'information' in choice['label'].lower()
    assert client.post(prefix+'/resolutions',json={'version':sample['version'],'finding_id':finding['id'],'action':'unknown','choice_id':'keep_open','owner':'Security lead'}).status_code==202
    updated=finish(client,sample['id'])
    saved=next(f for f in updated['report']['findings'] if f['id']==finding['id'])
    assert saved['status']=='open' and saved['owner']=='Security lead' and saved['choice_id']=='keep_open'


def test_dropdown_risk_choice_does_not_close_underlying_gap(client,sample):
    prefix=f"/api/cases/{sample['id']}";finding=sample['report']['findings'][0]
    assert client.post(prefix+'/resolutions',json={'version':sample['version'],'finding_id':finding['id'],'action':'accept_risk','choice_id':'accept_risk'}).status_code==202
    updated=finish(client,sample['id'])
    assert next(f for f in updated['report']['findings'] if f['id']==finding['id'])['status']=='risk_accepted'


def test_dropdown_rejects_forged_or_mismatched_decision_choice(client,sample):
    prefix=f"/api/cases/{sample['id']}";finding=sample['report']['findings'][0]
    body={'version':sample['version'],'finding_id':finding['id'],'action':'confirm','choice_id':'keep_open'}
    assert client.post(prefix+'/resolutions',json=body).status_code==400
    body['choice_id']='invented-approval'
    assert client.post(prefix+'/resolutions',json=body).status_code==400


def test_every_finding_type_has_context_specific_handling_choices():
    from backend.app.schemas import Candidate
    from backend.app.workflow import clarification_choices
    expected={'potential_conflict':'statements','missing_information':'information','unresolved_dependency':'dependent','unsupported_assumption':'assumption','possibly_outdated':'updated','clarification_needed':'confirmed'}
    for kind,word in expected.items():
        candidate=Candidate(check_id='test',title='A test finding',type=kind,priority='important',explanation='Context',impact='Planning',uncertainty='Needs confirmation',question='What should we do?',recommended_action='Clarify',evidence_ids=[])
        choices=clarification_choices(candidate,[])
        pending=next(c for c in choices if c.id=='keep_open')
        assert word in pending.label.lower() and pending.action=='unknown'
        assert len(choices)>=3
