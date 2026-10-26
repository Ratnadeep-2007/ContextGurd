"""Explicit, isolated live-model check using fictional conversation data only."""
import argparse
import json
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    if not parser.parse_args().live:
        parser.error('Pass --live to send only the built-in fictional text to the configured model providers.')
    from dotenv import load_dotenv
    from app.intake import Intake
    from app.storage import Store
    load_dotenv(ROOT / '.env', override=False)
    folder = ROOT / 'artifacts' / 'conversation-live' / uuid4().hex
    folder.mkdir(parents=True)
    service = Intake(Store(folder / 'check.sqlite3'))
    try:
        user = service.create_user('Fictional live reviewer', uuid4().hex)
        orchid = service.create_project(user, 'Orchid', 'The internal analytics pilot v2. Its pilot date must be agreed.', 'Can the Orchid v2 internal pilot proceed?')
        cedar = service.create_project(user, 'Cedar', 'The mobile security project. Security approval is a prerequisite.', 'Is Cedar security approval complete?')
        source = service.create_source(user, 'manual', 'fictional-live-meeting', 'Fictional mixed-project meeting')
        text = ('Orchid team: The pilot release is January 18, for the v2 internal pilot.\n'
                'Orchid sponsor: The pilot release is January 25, for that same v2 internal pilot.\n'
                'We talked about lunch and our weekend.\n'
                'Cedar team: The security approval is pending. The mobile release requires a named security approver.')
        job, _ = service.create_intake(user, {'sources': [{'source_id': source['id'], 'passages': [
            {'item_id': 'fictional-transcript', 'text': text, 'author': 'Fictional participants', 'location': 'Fictional meeting'}]}],
            'project_ids': [orchid['id'], cedar['id']], 'consent': True, 'model_consent': True})
        service.process_intake(job['id'])
        job = service.store.get('intake', job['id'])
        reviews = [service.get_review(user, rid) for rid in job['review_ids']]
        invalid = sum(c['quote'] not in service.store.get('evidence', c['evidence_id'])['text']
                      for r in reviews for f in r['findings'] for c in f['citations'])
        retained = json.dumps(service.store.all('evidence'))
        result = {'status': job['status'], 'error': job['error'], 'routing_providers': job['providers'],
                  'review_providers': [r['provider'] for r in reviews], 'review_count': len(reviews),
                  'findings': [{'project_id': r['project_id'], 'title': f['title'], 'kind': f['kind']}
                               for r in reviews for f in r['findings']],
                  'invalid_citations': invalid, 'discarded_units': job['discarded_units'],
                  'chatter_retained': 'lunch and our weekend' in retained,
                  'raw_input_removed': job['input'] == {}, 'artifact': str(folder.relative_to(ROOT))}
        result['passed'] = (job['status'] == 'complete' and len(reviews) == 2 and invalid == 0 and
                            not result['chatter_retained'] and result['raw_input_removed'] and
                            any(f['kind'] == 'potential_conflict' for f in result['findings']))
        (folder / 'results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2))
        return 0 if result['passed'] else 1
    finally:
        service.store.db.close()


if __name__ == '__main__':
    raise SystemExit(main())
