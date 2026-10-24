"""Isolated project-memory browser fixture. Scripted analysis; no live model calls."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT);sys.path.insert(0,str(ROOT))
os.environ['CONTEXTGUARD_DB']=str(ROOT/'artifacts'/'project-memory'/f'browser-{uuid4().hex}.sqlite3')
from backend.app import main
from backend.app.ingestion import parse_source
from backend.app.project_memory import Mem0Index, decision_sources
from backend.app.schemas import AnswerOption, Candidate, Case, Criterion, Evidence, Resolution, Run, Trace
from backend.app.workflow import fingerprint, verify

main.configured=lambda:[SimpleNamespace(name='controlled-test',model='manual-browser-fixture-no-live')]
app=main.create_app(memory_index=Mem0Index(base_url=''))
store=app.state.store
project=store.create_project('Synora - memory browser test')
store.create_project('Separate product - memory browser test')
check=Criterion(id='dates',title='Pilot timing',description='Clarify the pilot milestone.')
source_case=Case(title='Synora earlier review - controlled fixture',goal='Confirm the Synora pilot target',project_id=project.id,criteria=[check],sources=[parse_source(p.name,p.read_bytes()) for p in sorted((ROOT/'synora-review-pack').glob('0[1-6]-*.md'))])
evidence=[]
for i,(name,needle) in enumerate([('01-product-brief.md','December 7, 2026'),('04-release-checklist.md','January 18, 2027')]):
    source=next(s for s in source_case.sources if s.name==name)
    passage=next(p for p in source.passages if needle in p.text)
    evidence.append(Evidence(id=f'e{i}',check_id='dates',passage_id=passage.id,quote=passage.text))
candidate=Candidate(check_id='dates',title='Synora pilot target',type='potential_conflict',priority='important',explanation='The synthetic drafts propose different target dates.',impact='Clarify pilot planning.',uncertainty='No authority is established by the draft labels.',question='Which pilot target should the team follow?',recommended_action='Record the project lead clarification.',evidence_ids=['e0','e1'])
source_case.report=verify(source_case,[check],evidence,[candidate],['Controlled fixture; no model inference.'])
finding=source_case.report.findings[0]
source_case.resolutions.append(Resolution(finding_id=finding.id,action='confirm',answer='January 18, 2027 is the selected pilot target.',owner='Synthetic project lead',source_fingerprint=fingerprint(source_case),finding_title=finding.title,finding_question=finding.question,source_snapshot=decision_sources(source_case,finding)))
source_case.run=Run(status='completed')
store.save(source_case,create=True)

def controlled_analyze(case,progress):
    for stage in ['Planning checks','Finding source evidence','Challenging assumptions']:
        progress(stage)
    passage=next(p for s in case.sources for p in s.passages if 'December 7, 2026' in p.text)
    evidence=[Evidence(id='current-date',check_id='dates',passage_id=passage.id,quote=passage.text)]
    finding=Candidate(check_id='dates',title='Confirm whether the earlier pilot target changed',type='clarification_needed',priority='important',explanation='The current note proposes December 7. Compare it with the earlier user clarification shown in project memory.',impact='Pilot timing needs confirmation.',uncertainty='The prior answer does not approve this new proposal.',question='Does December 7 replace the earlier January 18 target?',recommended_action='Reconfirm the target with the project lead.',evidence_ids=['current-date'],answer_options=[AnswerOption(text='December 7, 2026',evidence_ids=['current-date'])])
    return verify(case,[check],evidence,[finding],['Controlled browser fixture: scripted model output, not live AI.'],[Trace(role=r,provider='controlled-test',model='manual-fixture',duration_ms=0) for r in ['Planner','Evidence','Challenge']])

main.analyze=controlled_analyze
if __name__=='__main__':
    import uvicorn
    print('CONTROLLED PROJECT-MEMORY TEST SERVER. No live model calls.',flush=True)
    uvicorn.run(app,host='127.0.0.1',port=8019)
