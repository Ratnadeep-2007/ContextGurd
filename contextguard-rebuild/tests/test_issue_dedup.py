import copy
import sqlite3
import json
import pytest
from app.contracts import Analysis
from app.providers import ProviderFailure
from app.review import Reviews
from app.service import Rejected
from test_routing import env
from scripts.reset_test_content import reset_content


def proposal(rows, **extra):
    return dict(kind='potential_conflict', issue_key='pilot-date', title='Pilot date disagreement',
        impact='The same pilot has two dates.', question='Which pilot date is approved?',
        next_action='Ask the project owner.', priority='medium', uncertainty='Approval is absent.',
        citations=[{'evidence_id': e['id'], 'quote': e['text']} for e in rows],
        same_scope=True, same_version=True, same_period=True, **extra)


def prepared(env):
    service, owner, other, project, second, source = env
    reviews=Reviews(service.store)
    rows=service.ingest(owner, {'source_id':source['id'],'project_id':project['id'],'consent':True,
        'passages':[{'item_id':'a','text':'The pilot date is December 7.'},
                    {'item_id':'b','text':'The pilot date is January 18.'}]})
    return reviews, owner, project, source, rows


def test_rephrased_duplicate_merges_citations_and_retains_distinct_topics(env):
    r, owner, project, source, rows=prepared(env)
    first=proposal(rows)
    second=copy.deepcopy(first)
    second.update(title='Unresolved schedule choice',priority='high',question='Who confirms the date?')
    third=copy.deepcopy(first)
    third.update(issue_key='memory-approval',title='Memory approval policy',question='Who approves memory changes?')
    review={'memory':[],'failures':[],'findings':[]}
    r._keep_findings(review, Analysis(findings=[first,second,third],limitations=['Controlled']).findings,
                     rows,project,set(),[])
    assert len(review['findings'])==2
    assert review['findings'][0]['priority']=='high'
    assert len(review['findings'][0]['citations'])==2
    assert review['findings'][0]['related_questions']==['Who confirms the date?']


def test_same_title_different_versions_stay_separate(env):
    r, owner, project, source, rows=prepared(env)
    first=proposal(rows)
    second=copy.deepcopy(first)
    first['title']='Pilot v1 date disagreement'
    second['title']='Pilot v2 date disagreement'
    review={'memory':[],'failures':[],'findings':[]}
    r._keep_findings(review,Analysis(findings=[first,second],limitations=['Controlled']).findings,
                     rows,project,set())
    assert len(review['findings'])==2


def test_repeated_unchanged_review_reuses_id_and_does_not_call_model(env):
    r, owner, project, source, rows=prepared(env)
    class Good:
        def analyze(self,*args,**kwargs):
            return Analysis(findings=[proposal(rows)],limitations=['Controlled']), 'Controlled'
    r.providers=Good()
    first=r.analyze(owner,project['id'],'Check the pilot',[source['id']],consent=True)
    class Broken:
        def analyze(self,*args,**kwargs):
            raise AssertionError('Unchanged review must be reused')
    r.providers=Broken()
    second=r.analyze(owner,project['id'],'Check the pilot',[source['id']],consent=True)
    assert second['id']==first['id']
    assert len(r.store.all('review'))==1


def test_failed_intake_retry_replaces_review_without_duplicate_card(env):
    r, owner, project, source, rows=prepared(env)
    class Broken:
        def analyze(self,*args,**kwargs):
            raise ProviderFailure('Controlled failure')
    r.providers=Broken()
    first=r.analyze(owner,project['id'],'Check the pilot',[source['id']],consent=True,intake_id='job1')
    class Good:
        def analyze(self,*args,**kwargs):
            return Analysis(findings=[proposal(rows)],limitations=['Controlled']), 'Controlled'
    r.providers=Good()
    second=r.analyze(owner,project['id'],'Check the pilot',[source['id']],consent=True,intake_id='job1')
    assert second['id']==first['id'] and second['status']=='complete'
    assert len(r.store.all('review'))==1


def test_dataset_reset_keeps_setup_and_blocks_active_workers(tmp_path):
    p=tmp_path/'reset.sqlite3'
    c=sqlite3.connect(p)
    c.execute('CREATE TABLE records(kind TEXT,id TEXT,workspace TEXT,body TEXT)')
    for kind in ['user','project','connection_check','decision','review','evidence','source']:
        c.execute('INSERT INTO records VALUES(?,?,?,?)',(kind,kind,'w',json.dumps({'id':kind})))
    c.execute('INSERT INTO records VALUES(?,?,?,?)',('intake','job','w',json.dumps({'id':'job','status':'analyzing'})))
    c.commit()
    with pytest.raises(RuntimeError):reset_content(p)
    assert c.execute('SELECT count(*) FROM records').fetchone()[0]==8
    c.execute("UPDATE records SET body=? WHERE kind='intake'",(json.dumps({'id':'job','status':'failed'}),));c.commit()
    removed=reset_content(p)
    assert removed['review']==1 and removed['decision']==1
    assert {r[0] for r in c.execute('SELECT kind FROM records')}=={'user','project','connection_check'}
    c.close()


def test_same_conflict_additional_passages_merge_without_losing_evidence(env):
    r, owner, project, source, rows=prepared(env)
    extra=r.ingest(owner, {'source_id':source['id'],'project_id':project['id'],'consent':True,
        'passages':[{'item_id':'c','text':'The pilot is still proposed for December 7.'}]})
    first=proposal(rows)
    second=proposal([rows[1],extra[0]])
    second['title']='Confirm the proposed pilot schedule'
    review={'memory':[],'failures':[],'findings':[]}
    r._keep_findings(review,Analysis(findings=[first,second],limitations=['Controlled']).findings,
                     rows+extra,project,set())
    assert len(review['findings'])==1
    assert {c['evidence_id'] for c in review['findings'][0]['citations']}=={e['id'] for e in rows+extra}


def test_rejected_citation_marks_review_failed(env):
    r, owner, project, source, rows=prepared(env)
    broken=proposal(rows)
    broken['citations'][0]['quote']='This was invented.'
    class BadCitation:
        def analyze(self,*args,**kwargs):
            return Analysis(findings=[broken],limitations=['Controlled']), 'Controlled'
    r.providers=BadCitation()
    review=r.analyze(owner,project['id'],'Check the pilot',[source['id']],consent=True)
    assert review['status']=='failed' and review['failures']
    assert not review['findings']


def test_reset_explicitly_stopped_server_can_clear_interrupted_job(tmp_path):
    p=tmp_path/'interrupted.sqlite3'
    c=sqlite3.connect(p)
    c.execute('CREATE TABLE records(kind TEXT,id TEXT,workspace TEXT,body TEXT)')
    c.execute('INSERT INTO records VALUES(?,?,?,?)',('intake','job','w',json.dumps({'status':'analyzing'})))
    c.commit()
    assert reset_content(p,server_stopped=True)=={'intake':1}
    assert c.execute('SELECT count(*) FROM records').fetchone()[0]==0
    c.close()
