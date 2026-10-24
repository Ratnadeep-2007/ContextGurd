"""Run the fixed LIVE evaluation only when explicitly requested; no fabricated scores."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.chdir(ROOT)
from dotenv import load_dotenv
load_dotenv(ROOT/'.env')
from backend.app.ingestion import parse_source
from backend.app.providers import configured
from backend.app.schemas import Case, default_criteria, now
from backend.app.workflow import analyze

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true',help='Send fictional fixtures to configured providers; incurs API usage.')
    args=parser.parse_args()
    cases=json.loads((ROOT/'evaluation/cases.json').read_text())
    if not args.live:
        print(f'{len(cases)} fixed evaluation bundles ready. Live detection accuracy is NOT measured. Run with --live after configuring API access.')
        raise SystemExit(0)
    if not configured():
        raise SystemExit('No API keys configured. Add them locally to .env; no evaluation results were generated.')
    results=[]
    for entry in cases:
        case=Case(title=entry['id'],goal=entry['goal'],criteria=default_criteria(),sources=[parse_source(f"source-{i+1}.txt",text.encode()) for i,text in enumerate(entry['sources'])])
        try:
            report=analyze(case,lambda stage: print(entry['id']+': '+stage,flush=True))
            types={f.type for f in report.findings}
            passed=set(entry['expected_types'])<=types and not set(entry['forbidden_types'])&types
            results.append({'id':entry['id'],'type_level_check_passed':passed,'report':report.model_dump(),'human_evidence_review':'pending','note':entry['note']})
        except Exception as exc:
            results.append({'id':entry['id'],'error':str(exc),'type_level_check_passed':False})
    target=ROOT/'artifacts/live-evaluation.json';target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps({'created_at':now(),'method':'Coarse expected/forbidden finding-type checks; not evidence-support precision or human-verified accuracy.','results':results},indent=2),encoding='utf-8')
    print(f'Saved {target}. Review evidence manually; do not present type-level checks as semantic accuracy.')
