"""Isolated Graphite & Cobalt design preview with fictional Synora evidence only."""
import argparse
import sys
from pathlib import Path
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    import uvicorn
    from app.api import create_app
    from app.contracts import Analysis
    from app.providers import ProviderFailure
    class DesignProvider:
        def analyze(self, goal, evidence, decisions, prior_findings=None):
            by_name={e['location']:e for e in evidence}
            specs=[
                ('pilot-date','Pilot date','Which pilot date is approved?', ['01-product-brief.md','02-architecture-notes.md'], 'Conflicting dates for the first pilot.'),
                ('atlas-evidence','Atlas edits as evidence','Should saved Atlas edits become evidence?', ['03-meeting-notes.md','05-integration-scope.md'], 'Read-only view or saved edits as evidence.'),
                ('memory-approval','Memory approval','Do requirement changes need member review?', ['02-architecture-notes.md','06-project-lead-email.md'], 'Member review or automatic writes.'),
                ('project-routing','Project routing','Who confirms ambiguous project routing?', ['02-architecture-notes.md','06-project-lead-email.md'], 'Human confirmation or nearest-project routing.'),
                ('owners-approval','Owners and sign-off','Who owns the unresolved pilot decisions?', ['03-meeting-notes.md','04-release-checklist.md'], 'No accountable owner or final approval.')]
            findings=[]
            for key,title,question,names,impact in specs:
                quotes=[]
                for name in names:
                    row=by_name[name]
                    # First sentence is exact source text; dates remain distinct.
                    lines=row['text'].split('\n')
                    quote=lines[-1] if (key in {'memory-approval','project-routing'} and name=='02-architecture-notes.md') or (key=='owners-approval' and name=='03-meeting-notes.md') else lines[0]
                    quotes.append({'evidence_id':row['id'],'quote':quote})
                findings.append({'kind':'missing_information' if key=='owners-approval' else 'potential_conflict',
                    'issue_key':key,'title':title,'question':question,'impact':impact,
                    'next_action':'Select the statement the project should follow, or provide another answer.',
                    'priority':'high','citations':quotes,
                    'uncertainty':'Both statements refer to the same pilot. No approval is recorded.' if key=='pilot-date' else 'This fictional policy discussion has no recorded approval.',
                    'same_scope':True,'same_version':True,'same_period':True})
            return Analysis(findings=findings,limitations=['Fictional design fixture; no model or external source calls.']), 'Fictional design fixture'
        def classify(self,*args,**kwargs):
            raise ProviderFailure('This isolated design preview does not contact models.')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8056)
    args=parser.parse_args()
    if not 1024<=args.port<=65535:parser.error('Use a local development port.')
    db=ROOT/'artifacts'/('design-preview-'+uuid4().hex+'.sqlite3')
    app=create_app(db,providers=DesignProvider(),load_settings=False)
    service=app.state.service
    owner=service.create_user('Preview owner','fictional-design-password')
    project=service.create_project(owner,'Synora','Fictional first internal pilot: date, Atlas evidence, memory review, routing and decision owners.','Is the first Synora pilot ready?')
    texts={
        '01-product-brief.md':'The first internal pilot is planned for December 7, 2026.\nAtlas is a read-only generated view; canvas edits are not evidence.',
        '02-architecture-notes.md':'The working architecture plan targets January 18, 2027 for the first internal pilot.\nChanges stay pending until member review. Ambiguous evidence needs human routing confirmation.',
        '03-meeting-notes.md':'Saved Atlas edits should become evidence, according to the unresolved meeting proposal.\nNo decision was taken. No owner was named.',
        '04-release-checklist.md':'All readiness items are unchecked; there are no owners, completion evidence or final approval.',
        '05-integration-scope.md':'Atlas is read-only; direct Atlas-edit ingestion and auto-routing are outside the pilot.',
        '06-project-lead-email.md':'The lead proposes automatic memory writes without member review and nearest-project routing.\nNeither proposal records completed approval.'}
    sources=[]
    for name,text in texts.items():
        source=service.create_source(owner,'manual',name,name)
        service.ingest(owner,{'source_id':source['id'],'project_id':project['id'],'consent':True,'test_mode':True,
                              'passages':[{'item_id':'passage-1','text':text,'location':name}]})
        sources.append(source['id'])
    review=service.analyze(owner,project['id'],project['goal'],sources,consent=True)
    review['test_mode']=True
    service.store.put('review',review)
    print('Fictional design preview only. Fresh isolated database: '+str(db),flush=True)
    uvicorn.run(app,host='127.0.0.1',port=args.port,access_log=False,log_level='warning')


if __name__=='__main__':main()
